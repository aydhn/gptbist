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
