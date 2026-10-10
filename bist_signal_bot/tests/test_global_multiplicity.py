import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.global_multiplicity import global_dsr
from bist_signal_bot.edge_validation.ledger import TrialLedger


def _series(mu, n=500, seed=0):
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(mu, 0.01, n), index=pd.date_range("2020-01-01", periods=n, freq="B"))


def test_global_dsr_is_not_looser_than_family_dsr(tmp_path):
    led = TrialLedger(path=tmp_path / "t.sqlite")
    for i in range(3):
        led.record_trial(f"a{i}", "a", {"i": i}, "1d", "u", _series(0.0004, seed=i), strategy_family="fa_daily_xs_ew")
    for j in range(40):
        led.record_trial(f"b{j}", "b", {"j": j}, "1d", "u", _series(0.0, seed=100 + j), strategy_family="fb_daily_xs_ew")
    r = global_dsr(led, "fa_daily_xs_ew")
    assert r["n_global"] == 43 and r["n_family"] == 3
    assert r["dsr_global"] <= r["dsr_family"] + 1e-12


def test_global_dsr_handles_empty_family(tmp_path):
    led = TrialLedger(path=tmp_path / "t.sqlite")
    r = global_dsr(led, "missing_daily_xs_ew")
    assert r["passes"] is None
