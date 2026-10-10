"""fixed_primary: the pre-declared centre is selected even when a neighbour has a higher Sharpe; None = best Sharpe."""
import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.gate import CandidateGate, GateConfig
from bist_signal_bot.edge_validation.ledger import TrialLedger
from bist_signal_bot.edge_validation.runner_daily import run_family_daily
from bist_signal_bot.edge_validation.xsection import DailyContext
from bist_signal_bot.tests.test_xsection_daily import make_panel

H = 5


class OracleFamily:
    """Look-ahead ORACLE on purpose (test only): score = forward return + noise*``noise``. Lower noise => higher Sharpe."""
    name = "oracle_test"
    default_grid = {"noise": [0.0, 5.0]}

    def valid(self, params):
        return True

    def score(self, ctx, params):
        fwd = ctx.close.shift(-H) / ctx.close - 1.0
        rng = np.random.default_rng(1)
        return fwd + float(params["noise"]) * 0.05 * pd.DataFrame(rng.normal(size=fwd.shape), index=fwd.index,
                                                                   columns=fwd.columns)


def _run(tmp_path, fixed):
    panel = make_panel(3, n_sym=30, days=700)
    bm = pd.DataFrame({s: d["close"] for s, d in panel.items()}).mean(axis=1)
    ctx = DailyContext.from_panel(panel, bm, min_adv=5e6)
    led = TrialLedger(tmp_path / "t.sqlite")
    grid = {"noise": [5.0, 0.0]}  # centre first, the better neighbour second
    return run_family_daily(OracleFamily(), ctx, (H,), grid, 8, led, CandidateGate(GateConfig(), save=False),
                            save_report=False, benchmark="ew_universe", fixed_primary=fixed)


def _sharpes(res):
    return {t["params"]["noise"]: t["net_sharpe_period"] for t in res.trials}


def test_fixed_primary_selects_centre_even_if_neighbour_sharpe_is_higher(tmp_path):
    res = _run(tmp_path, {"noise": 5.0})
    sh = _sharpes(res)
    assert sh[0.0] > sh[5.0]  # the neighbour really is better
    sel = next(t for t in res.trials if t["trial_id"] == res.selected_trial_id)
    assert sel["params"] == {"noise": 5.0}


def test_no_fixed_primary_keeps_best_sharpe_selection(tmp_path):
    res = _run(tmp_path, None)
    sel = next(t for t in res.trials if t["trial_id"] == res.selected_trial_id)
    assert sel["params"] == {"noise": 0.0}
