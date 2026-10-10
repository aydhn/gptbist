"""Cross-family multiplicity check (tightening only; never replaces the CandidateGate).

The gate deflates the Sharpe ratio by the number of trials *within one family*. When many families
(and horizons) are screened, the chance that at least one passes is much higher. This module
re-computes the Deflated Sharpe Ratio of a family's best trial with N = all trials of the screened
families (ledger families sharing a suffix, e.g. ``_daily_xs_ew``), as an extra, conservative diagnostic.
Dispersion of Sharpes across heterogeneous families inflates E[max SR], so this is intentionally harsh.
"""
from __future__ import annotations

from typing import Dict, Optional

import numpy as np

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


def global_dsr_robust(ledger: TrialLedger, family: str, suffix: str, trial_id: Optional[str] = None,
                      dsr_min: float = 0.95, mad_k: float = 3.5) -> Dict[str, Optional[float]]:
    """Global-multiplicity DSR used as a GATING robustness criterion (v2 mode).

    * pool = ledger families ending with the SAME statistic ``suffix`` (e.g. ``_daily_xs_ew2``), placebo excluded, so
      only trials of the identical evaluated statistic are mixed;
    * N = ALL trials in the pool (honest count, never trimmed);
    * Sharpe dispersion = MAD-trimmed variance of the pool's per-period Sharpes (``mad_trimmed_variance``): trimming
      only removes junk outliers from the dispersion; it can never reduce N;
    * evaluated trial = ``trial_id`` when given and recorded with a return series, else the family's best-Sharpe trial;
    * ``passes`` False/None (unavailable) both fail closed in the runner.
    """
    fams = [r[0] for r in ledger._query("SELECT DISTINCT strategy_family FROM trials")]
    pool = [f for f in fams if f.endswith(suffix) and "placebo" not in f]
    n_global = sum(ledger.n_trials(f) for f in pool)
    sh = np.concatenate([ledger.trial_sharpes(f) for f in pool]) if pool else np.array([])
    var_raw = float(np.var(sh, ddof=1)) if sh.size >= 2 else float("nan")
    var = mad_trimmed_variance(sh, mad_k)
    out: Dict[str, Optional[float]] = {"family": family, "suffix": suffix, "n_global": n_global,
                                       "n_pool_families": len(pool), "variance_raw": var_raw,
                                       "variance_trimmed": var, "mad_k": mad_k, "dsr_min": dsr_min,
                                       "dsr_global": None, "dsr_family": None, "passes": None}
    m = ledger.returns_matrix(family)
    if m.shape[1] == 0 or not np.isfinite(var):
        return out
    tid = trial_id if trial_id in m.columns else max(
        m.columns, key=lambda c: (lambda v: v if np.isfinite(v) else -np.inf)(st.sharpe(m[c].to_numpy(float))))
    r = m[tid].to_numpy(float)
    n_fam, var_fam = ledger.n_trials(family), ledger.trial_sharpe_variance(family)
    out["trial_id"] = tid
    out["sharpe_annual"] = float(st.sharpe(r) * np.sqrt(ANN))
    out["n_family"] = n_fam
    out["dsr_family"] = float(st.deflated_sharpe_ratio(r, max(n_fam, 1), var_fam if np.isfinite(var_fam) else 0.0))
    dg = float(st.deflated_sharpe_ratio(r, max(n_global, 1), var))
    out["dsr_global"] = dg if np.isfinite(dg) else None
    out["expected_max_sharpe_global_annual"] = float(st.expected_max_sharpe(max(n_global, 1), var) * np.sqrt(ANN))
    out["passes"] = bool(np.isfinite(dg) and dg >= dsr_min)
    return out
