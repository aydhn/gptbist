from types import SimpleNamespace

import numpy as np
import pandas as pd

from bist_signal_bot.model_loop.daily_lifecycle import DailyDriftMonitor
from bist_signal_bot.model_loop.drift_monitor import DriftMonitor, bh_adjust

S = SimpleNamespace()
SL = SimpleNamespace(DAILY_DRIFT_LEGACY=True)


def panel(rng, days, m=60, mkt_shift=0.0, score_shift=0.0, n_mkt=3, n_cs=6, start=0):
    dates = np.repeat(pd.date_range("2020-01-01", periods=start + days)[start:].values, m)
    df = pd.DataFrame({"_date": dates})
    for k in range(n_mkt):  # market-level: one value per date, shared by all symbols
        v = rng.normal(size=days) + (mkt_shift if k == 0 else 0.0)
        df[f"mkt{k}"] = np.repeat(v, m)
    for k in range(n_cs):
        df[f"cs{k}"] = rng.normal(size=days * m)
    df["score"] = rng.normal(size=days * m) + score_shift
    return df


def test_bh_adjust_monotone():
    a = bh_adjust([0.01, 0.04, 0.03, 0.5])
    assert np.all(a >= np.array([0.01, 0.04, 0.03, 0.5]) - 1e-12) and a.max() <= 1.0
    assert abs(a[0] - 0.04) < 1e-9


def test_iid_null_low_false_alarm_rate():
    rng = np.random.default_rng(0)
    mon = DailyDriftMonitor(S)
    fa = sum(mon.check_features(panel(rng, 250), panel(rng, 60)).retrain for _ in range(200))
    assert fa / 200 < 0.10


def test_market_level_constant_shift_is_caught_in_effective_sample():
    rng = np.random.default_rng(1)
    ref, cur = panel(rng, 250, mkt_shift=0.0), panel(rng, 60, mkt_shift=0.0)
    # shift ALL market-level features by a constant (3 of 10 features -> fraction 0.3 >= 0.2)
    for k in range(3):
        cur[f"mkt{k}"] = cur[f"mkt{k}"] + 1.5
    dec = DailyDriftMonitor(S).check_features(ref, cur)
    assert dec.retrain and dec.details["n_significant_bh"] >= 3


def test_single_feature_shift_does_not_retrain():
    rng = np.random.default_rng(2)
    ref, cur = panel(rng, 250), panel(rng, 60, mkt_shift=2.0)  # only mkt0 shifted (1/9 features)
    dec = DailyDriftMonitor(S).check_features(ref, cur)
    assert not dec.retrain and dec.details["n_significant_bh"] >= 1


def test_score_shift_triggers_retrain():
    rng = np.random.default_rng(3)
    dec = DailyDriftMonitor(S).check_features(panel(rng, 250), panel(rng, 60, score_shift=1.0))
    # score noise dominates row-level; the daily mean shift of 1.0 is huge vs daily-mean sd (~0.13)
    assert dec.retrain and any(r.startswith("score_drift") for r in dec.reasons)


def test_legacy_flag_restores_row_level_behaviour():
    rng = np.random.default_rng(4)
    ref, cur = panel(rng, 250), panel(rng, 60, mkt_shift=0.6)
    legacy = DailyDriftMonitor(SL).check_features(ref, cur)
    assert legacy.details.get("legacy") is None and all(np.isnan(f.p_adj) for f in legacy.findings)
    new = DailyDriftMonitor(S).check_features(ref, cur)
    assert new.details["legacy"] is False


def test_plain_frames_still_work():
    rng = np.random.default_rng(5)
    ref = pd.DataFrame({"a": rng.normal(size=500), "b": rng.normal(size=500)})
    assert DriftMonitor(S).check_features(ref, ref.assign(a=rng.normal(size=500) + 3, b=rng.normal(size=500) + 3)).retrain


def _wide(rng, days, m, n_mkt, n_cs, shift_k, shift=1.5):
    df = panel(rng, days, m=m, n_mkt=n_mkt, n_cs=n_cs)
    for k in range(shift_k):
        df[f"mkt{k}"] = df[f"mkt{k}"] + shift
    return df


def test_cross_section_heavy_30_features_three_market_shifts_below_fraction():
    rng = np.random.default_rng(10)
    ref = _wide(rng, 250, 20, 6, 24, 0)
    cur = _wide(rng, 60, 20, 6, 24, 3)  # 3 of 30 testable features shift => 0.10 < alert_frac 0.2
    dec = DailyDriftMonitor(S).check_features(ref, cur)
    assert dec.details["n_features"] == 30 and dec.details["n_significant_bh"] >= 3
    assert not dec.retrain
    cur6 = _wide(rng, 60, 20, 6, 24, 6)  # 6/30 = 0.2 => retrain
    assert DailyDriftMonitor(S).check_features(ref, cur6).retrain


def test_constant_features_excluded_from_denominator_and_min_two_significant():
    rng = np.random.default_rng(11)
    ref, cur = panel(rng, 250, n_mkt=2, n_cs=0), panel(rng, 60, n_mkt=2, n_cs=0)
    for k in range(5):
        ref[f"const{k}"] = 0.0
        cur[f"const{k}"] = 0.0
    cur["mkt0"] = cur["mkt0"] + 2.0  # 1 shifted of 2 testable: 0.5 >= 0.2 but n_sig=1 < 2 => no retrain
    dec = DailyDriftMonitor(S).check_features(ref, cur)
    assert dec.details["n_features"] == 2 and dec.details["n_significant_bh"] == 1 and not dec.retrain
    cur["mkt1"] = cur["mkt1"] + 2.0
    assert DailyDriftMonitor(S).check_features(ref, cur).retrain


def test_bare_driftmonitor_keeps_legacy_even_with_date_column():
    rng = np.random.default_rng(12)
    d = DriftMonitor(S).check_features(panel(rng, 250), panel(rng, 60))
    assert d.details.get("legacy") is None
