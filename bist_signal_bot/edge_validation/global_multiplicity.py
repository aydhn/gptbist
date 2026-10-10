"""Cross-family multiplicity check (tightening only; never replaces the CandidateGate).

The gate deflates the Sharpe ratio by the number of trials *within one family*. When many families
(and horizons) are screened, the chance that at least one passes is much higher. This module
re-computes the Deflated Sharpe Ratio of a family's best trial with N = all trials of the screened
families (ledger families sharing a suffix, e.g. ``_daily_xs_ew``), as an extra, conservative diagnostic.
Dispersion of Sharpes across heterogeneous families inflates E[max SR], so this is intentionally harsh.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation import stats as st
from bist_signal_bot.edge_validation.ledger import TrialLedger

ANN = 252


def global_dsr(ledger: TrialLedger, family: str, suffix: str = "_daily_xs_ew",
               dsr_min: float = 0.95) -> Dict[str, Optional[float]]:
    fams = [r[0] for r in ledger._query("SELECT DISTINCT strategy_family FROM trials")]
    pool = [f for f in fams if f.endswith(suffix) and "placebo" not in f]
    n_global = sum(ledger.n_trials(f) for f in pool)
    sh = np.concatenate([ledger.trial_sharpes(f) for f in pool]) if pool else np.array([])
    var = float(np.var(sh, ddof=1)) if sh.size >= 2 else float("nan")
    m = ledger.returns_matrix(family)
    if m.shape[1] == 0 or not np.isfinite(var):
        return {"family": family, "n_global": n_global, "dsr_global": None, "passes": None}
    srs = {c: st.sharpe(m[c].to_numpy(float)) for c in m.columns}
    best = max(srs, key=lambda k: srs[k] if np.isfinite(srs[k]) else -np.inf)
    n_fam, var_fam = ledger.n_trials(family), ledger.trial_sharpe_variance(family)
    dsr_f = st.deflated_sharpe_ratio(m[best].to_numpy(float), max(n_fam, 1), var_fam if np.isfinite(var_fam) else 0.0)
    dsr_g = st.deflated_sharpe_ratio(m[best].to_numpy(float), max(n_global, 1), var)
    return {"family": family, "best_trial": best, "sharpe_annual": float(srs[best] * np.sqrt(ANN)),
            "n_family": n_fam, "n_global": n_global, "dsr_family": float(dsr_f), "dsr_global": float(dsr_g),
            "expected_max_sharpe_global_annual": float(st.expected_max_sharpe(max(n_global, 1), var) * np.sqrt(ANN)),
            "passes": bool(np.isfinite(dsr_g) and dsr_g >= dsr_min)}


def mad_trimmed_variance(sh: np.ndarray, k: float = 3.5) -> float:
    """Sample variance of the Sharpes after dropping outliers with |x - median| > k * 1.4826 * MAD (robust z-score).
    Absurd junk strategies (huge |Sharpe| from a handful of events or degenerate series) would otherwise dominate the
    dispersion that sets E[max SR]. Falls back to the plain variance when MAD == 0 (nothing can be trimmed)."""
    sh = np.asarray(sh, dtype=float)
    sh = sh[np.isfinite(sh)]
    if sh.size < 2:
        return float("nan")
    med = float(np.median(sh))
    mad = float(np.median(np.abs(sh - med))) * 1.4826
    kept = sh if mad <= 0 else sh[np.abs(sh - med) <= k * mad]
    return float(np.var(kept, ddof=1)) if kept.size >= 2 else float("nan")


NEFF_DIST_THRESHOLD = 0.5  # trials with |corr| >= 0.5 (distance 1-|corr| <= 0.5) merge into one cluster
NEFF_MIN_PERIODS = 20


def effective_n(ledger: TrialLedger, pool: List[str], n_global: int, max_rowid: Optional[int] = None,
                min_universe: Optional[int] = None, threshold: float = NEFF_DIST_THRESHOLD) -> Optional[int]:
    """Effective number of independent trials in the pool (diagnostic ONLY; never used to reduce the gate's N).

    Deterministic ONC-lite: average-linkage hierarchical clustering on d = 1 - |corr| of the pool's return series
    (pairwise-observed), cut at a fixed distance ``threshold``. Trials without a return series (failed) each count as
    one cluster. Result is always <= ``n_global``. None when it cannot be computed."""
    try:
        from scipy.cluster.hierarchy import fcluster, linkage
        from scipy.spatial.distance import squareform
        frames = []
        for f in pool:
            m, mask = ledger.returns_matrix(f, with_mask=True, max_rowid=max_rowid, min_universe=min_universe)
            if m.shape[1]:
                frames.append(m.where(mask))
        n_cols = sum(fr.shape[1] for fr in frames)
        if n_cols == 0:
            return int(n_global) if n_global else None
        if n_cols == 1:
            return int(min(n_global, 1 + (n_global - n_cols)))
        raw = pd.concat(frames, axis=1)
        raw = raw.reindex(sorted(raw.columns), axis=1).sort_index()
        c = raw.corr(min_periods=NEFF_MIN_PERIODS).to_numpy(float)
        d = 1.0 - np.abs(c)
        d = np.where(np.isfinite(d), d, 1.0)
        d = np.clip((d + d.T) / 2.0, 0.0, 1.0)
        np.fill_diagonal(d, 0.0)
        labels = fcluster(linkage(squareform(d, checks=False), method="average"), t=float(threshold),
                          criterion="distance")
        return int(min(n_global, len(set(labels.tolist())) + max(int(n_global) - n_cols, 0)))
    except Exception:  # diagnostic only
        return None


def global_dsr_robust(ledger: TrialLedger, family: str, suffix: str, trial_id: Optional[str] = None,
                      dsr_min: float = 0.95, mad_k: float = 3.5, snapshot_rowid: Optional[int] = None,
                      min_universe: Optional[int] = None) -> Dict[str, Optional[float]]:
    """Global-multiplicity DSR used as a GATING robustness criterion (v2 mode).

    * pool = ledger families ending with the SAME statistic ``suffix`` (e.g. ``_daily_xs_ew2``), placebo excluded, so
      only trials of the identical evaluated statistic are mixed;
    * ``snapshot_rowid`` (optional) freezes the pool to ledger rows with rowid <= snapshot (batch-order independent
      verdicts); the evaluated family/trial must then be inside the snapshot, else the check is unavailable (fails closed);
    * ``min_universe`` (optional) drops trials recorded with a universe smaller than this from the Sharpe DISPERSION
      only (dev/smoke pollution); they still COUNT in N (``small_universe_count`` reports how many). The evaluated
      family is subject to the same filter (fail closed when it only has small-universe trials);
    * a given ``trial_id`` that is not available (outside snapshot/universe/no series) fails closed on every path:
      there is never a silent substitution by the best-Sharpe trial;
    * N = ALL trials in the pool (``n_global``: honest raw count, never trimmed or filtered; the gating DSR uses it);
    * ``n_effective`` / ``dsr_global_neff`` = correlation-clustered N and the DSR with it: DIAGNOSTIC only;
    * Sharpe dispersion = MAD-trimmed variance of the pool's per-period Sharpes (``mad_trimmed_variance``): trimming
      only removes junk outliers from the dispersion; it can never reduce N;
    * evaluated trial = ``trial_id`` when given and recorded with a return series, else the family's best-Sharpe trial;
    * ``passes`` False/None (unavailable) both fail closed in the runner.
    """
    snap, mu = snapshot_rowid, (int(min_universe) if min_universe else None)
    fams = ledger.families(suffix, snap)
    pool = [f for f in fams if "placebo" not in f]
    n_global = sum(ledger.n_trials(f, snap) for f in pool)  # honest N: small-universe trials still count
    n_in_dispersion = sum(ledger.n_trials(f, snap, mu) for f in pool)
    sh = np.concatenate([ledger.trial_sharpes(f, snap, mu) for f in pool]) if pool else np.array([])
    var_raw = float(np.var(sh, ddof=1)) if sh.size >= 2 else float("nan")
    var = mad_trimmed_variance(sh, mad_k)
    out: Dict[str, Optional[float]] = {"family": family, "suffix": suffix, "n_global": n_global,
                                       "n_pool_families": len(pool),
                                       "small_universe_count": int(n_global - n_in_dispersion), "variance_raw": var_raw,
                                       "variance_trimmed": var, "mad_k": mad_k, "dsr_min": dsr_min,
                                       "snapshot_rowid": snap, "min_universe": mu,
                                       "n_effective": None, "dsr_global_neff": None,
                                       "dsr_global": None, "dsr_family": None, "passes": None}
    m = ledger.returns_matrix(family, max_rowid=snap, min_universe=mu)
    if m.shape[1] == 0 or not np.isfinite(var):
        if m.shape[1] == 0 and (snap is not None or mu):
            out["error"] = "family_outside_snapshot_or_below_min_universe"
        return out
    if trial_id is not None and trial_id not in m.columns:
        out["error"] = "trial_outside_snapshot_or_below_min_universe"
        return out
    tid = trial_id if trial_id in m.columns else max(
        m.columns, key=lambda c: (lambda v: v if np.isfinite(v) else -np.inf)(st.sharpe(m[c].to_numpy(float))))
    r = m[tid].to_numpy(float)
    n_fam = ledger.n_trials(family, snap)
    sf = ledger.trial_sharpes(family, snap, mu)
    var_fam = float(np.var(sf, ddof=1)) if sf.size >= 2 else float("nan")
    out["trial_id"] = tid
    out["sharpe_annual"] = float(st.sharpe(r) * np.sqrt(ANN))
    out["n_family"] = n_fam
    out["dsr_family"] = float(st.deflated_sharpe_ratio(r, max(n_fam, 1), var_fam if np.isfinite(var_fam) else 0.0))
    dg = float(st.deflated_sharpe_ratio(r, max(n_global, 1), var))
    out["dsr_global"] = dg if np.isfinite(dg) else None
    out["expected_max_sharpe_global_annual"] = float(st.expected_max_sharpe(max(n_global, 1), var) * np.sqrt(ANN))
    neff = effective_n(ledger, pool, n_global, snap, mu)
    out["n_effective"] = neff
    if neff is not None:
        dn = float(st.deflated_sharpe_ratio(r, max(neff, 1), var))
        out["dsr_global_neff"] = dn if np.isfinite(dn) else None
    out["passes"] = bool(np.isfinite(dg) and dg >= dsr_min)  # RAW n_global only; N_eff never loosens the gate
    return out
