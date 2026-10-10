import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.edge_validation import families_daily_macro as fm
from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
from bist_signal_bot.edge_validation.gate import CandidateGate, GateConfig
from bist_signal_bot.edge_validation.ledger import TrialLedger
from bist_signal_bot.edge_validation.runner_daily import run_family_daily
from bist_signal_bot.edge_validation.xsection import (DailyContext, build_portfolio_events, check_score_causality,
                                                      nav_returns)
from bist_signal_bot.tests.test_xsection_daily import make_panel

NAMES = ["xs_rel_strength_index", "xs_rel_strength_sector", "xs_fx_sensitivity", "cal_turn_of_month",
         "cal_pre_holiday", "cal_month_end_reversal"]


def _bench_fx(panel, seed=5):
    idx = next(iter(panel.values())).index
    rng = np.random.default_rng(seed)
    bm = pd.Series(1000 * np.exp(np.cumsum(rng.normal(0.0004, 0.01, len(idx)))), index=idx)
    fx = pd.Series(10 * np.exp(np.cumsum(rng.normal(0.0008, 0.006, len(idx)))), index=idx)
    return bm, fx


@pytest.fixture(scope="module")
def ctx():
    p = make_panel(3, n_sym=30, days=700)
    bm, fx = _bench_fx(p)
    c = DailyContext.from_panel(p, bm, min_adv=5e6)
    fm.FX_SENSITIVITY.set_usdtry(fx)
    yield c
    fm.FX_SENSITIVITY.set_usdtry(None)


PARAMS = {"xs_rel_strength_index": {"lookback": 60, "adjust": "beta"},
          "xs_rel_strength_sector": {"lookback": 20, "n_clusters": 5, "corr_window": 120},
          "xs_fx_sensitivity": {"beta_window": 120, "thr": 0.5},
          "cal_turn_of_month": {"tiebreak": "momentum"}, "cal_pre_holiday": {"tiebreak": "liquidity"},
          "cal_month_end_reversal": {"lookback": 10}}


def test_registered_and_valid_default_grids():
    for n in NAMES:
        f = DAILY_FAMILIES[n]
        assert f.default_grid and all(f.valid(dict(zip(f.default_grid, v))) for v in zip(*f.default_grid.values()))


@pytest.mark.parametrize("name", NAMES)
def test_causal_deterministic_shape(ctx, name):
    f, p = DAILY_FAMILIES[name], PARAMS[name]
    check_score_causality(f, ctx, p)
    a, b = f.score(ctx, p), f.score(ctx, p)
    pd.testing.assert_frame_equal(a, b)
    assert a.shape == ctx.close.shape
    assert np.isfinite(a.to_numpy(float)).any()
    if hasattr(f, "rebalance_mask"):  # mask must be causal/deterministic too
        m1, m2 = f.rebalance_mask(ctx, p), f.rebalance_mask(ctx.truncate(400), p)
        assert m1.dtype == bool and m1.sum() > 3
        assert (m1.iloc[:400].to_numpy() == m2.to_numpy()).all()


@pytest.mark.parametrize("name", NAMES)
def test_short_history_and_nan_safe(name):
    p = make_panel(4, n_sym=10, days=40)
    bm, fx = _bench_fx(p)
    c = DailyContext.from_panel(p, bm, min_adv=5e6, min_history=5)
    fm.FX_SENSITIVITY.set_usdtry(fx)
    try:
        f = DAILY_FAMILIES[name]
        s = f.score(c, PARAMS[name])
        assert s.shape == c.close.shape
        assert not np.isinf(s.to_numpy(float)).any()
        build_portfolio_events(c, s, 3, 3, rebalance_mask=f.rebalance_mask(c, PARAMS[name])
                               if hasattr(f, "rebalance_mask") else None)
    finally:
        fm.FX_SENSITIVITY.set_usdtry(None)


def test_missing_inputs_raise(ctx):
    c = DailyContext.from_panel(make_panel(4, n_sym=5, days=300))
    with pytest.raises(ValueError):
        DAILY_FAMILIES["xs_rel_strength_index"].score(c, PARAMS["xs_rel_strength_index"])
    fm.FX_SENSITIVITY.set_usdtry(None)
    with pytest.raises(ValueError):
        DAILY_FAMILIES["xs_fx_sensitivity"].score(c, PARAMS["xs_fx_sensitivity"])
    fm.FX_SENSITIVITY.set_usdtry(_bench_fx(make_panel(3, n_sym=30, days=700))[1])


def test_index_none_adjust_is_rank_duplicate_of_momentum(ctx):
    s = DAILY_FAMILIES["xs_rel_strength_index"].score(ctx, {"lookback": 60, "adjust": "none"})
    m = DAILY_FAMILIES["xs_momentum"].score(ctx, {"lookback": 60, "skip": 0})
    assert (s.rank(axis=1).fillna(-1).to_numpy() == m.rank(axis=1).fillna(-1).to_numpy())[100:].all()


def test_sector_proxy_clusters_recover_planted_groups():
    rng = np.random.default_rng(0)
    days, idx = 500, pd.bdate_range("2020-01-01", periods=500)
    f = [rng.normal(0, 0.012, days) for _ in range(3)]
    panel = {}
    for k in range(18):
        r = f[k % 3] + rng.normal(0, 0.004, days) + 0.0002
        c = 50 * np.exp(np.cumsum(r))
        panel[f"S{k:02d}"] = pd.DataFrame({"open": c, "high": c, "low": c, "close": c, "volume": np.full(days, 2e6)}, index=idx)
    c = DailyContext.from_panel(panel, min_adv=5e6)
    lab = fm.XSRelStrengthSector().clusters(c, 3, 120).iloc[-1]
    for g in range(3):
        assert lab.iloc[g::3].nunique() == 1
    assert lab.nunique() == 3


def test_fx_sign_flips_with_regime(ctx):
    s = DAILY_FAMILIES["xs_fx_sensitivity"]
    hi = s.score(ctx, {"beta_window": 120, "thr": 0.0}).to_numpy(float)
    lo = s.score(ctx, {"beta_window": 120, "thr": 1e9}).to_numpy(float)  # always "stable" -> -beta
    ok = np.isfinite(hi) & np.isfinite(lo)
    assert ok.any() and np.allclose(np.abs(hi[ok]), np.abs(lo[ok]))
    pos = np.nanmean((hi[ok] * lo[ok]) < 0)  # rows where regime = depreciation flip the sign
    assert 0.1 < pos < 0.9


def test_calendar_dates():
    c = DailyContext.from_panel(make_panel(5, n_sym=5, days=800))
    tom = fm.CalTurnOfMonth().rebalance_mask(c, {})
    for t in tom.index[tom]:
        month_days = [d for d in fm._calendar_days(c) if (d.year, d.month) == (t.year, t.month)]
        assert month_days[-3] == t.date()
    ph = fm.CalPreHoliday().rebalance_mask(c, {})
    assert ph.sum() >= 4  # e.g. fixed national holidays 2019-2021
    me = fm.CalMonthEndReversal().rebalance_mask(c, {})
    assert 25 <= me.sum() <= 40


def test_mask_no_positions_outside_window_and_cash_earns(ctx):
    f, p = DAILY_FAMILIES["cal_turn_of_month"], PARAMS["cal_turn_of_month"]
    m = f.rebalance_mask(ctx, p)
    ev = build_portfolio_events(ctx, f.score(ctx, p), 5, 5, rebalance_mask=m).events
    assert len(ev) and set(ev["t0"].unique()) <= set(m.index[m])
    nav = nav_returns(ctx, ev, None)
    held = nav["holdings"] > 0
    assert 0 < held.mean() < 0.4
    assert np.allclose(nav.loc[~held, "ret"], ctx.cash_ret[~held])  # cash earns interest when flat
    # default (no mask) unchanged: more rebalances
    ev0 = build_portfolio_events(ctx, f.score(ctx, p), 5, 5).events
    assert ev0["t0"].nunique() > ev["t0"].nunique()


def test_runner_passes_mask(ctx, tmp_path):
    f = DAILY_FAMILIES["cal_turn_of_month"]
    r = run_family_daily(f, ctx, (5,), {"tiebreak": ["liquidity", "momentum"]}, 5, TrialLedger(tmp_path / "t.sqlite"),
                         CandidateGate(GateConfig(), save=False), save_report=False)
    assert len(r.trials) == 2 and all(t["error"] is None for t in r.trials)
    assert r.report["n_trials_ledger"] == 2
