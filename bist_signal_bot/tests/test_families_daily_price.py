"""Price/volume daily families: causality, NaN handling, determinism, semantics (offline synthetic panels)."""
import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
from bist_signal_bot.edge_validation.xsection import DailyContext, check_score_causality
from bist_signal_bot.tests.test_xsection_daily import make_panel

NAMES = ["xs_momentum_12_1", "xs_momentum_1_6", "xs_reversal", "xs_low_vol", "xs_low_beta", "xs_quality_proxy",
         "xs_volume_shock"]


def _grid(fam):
    keys = list(fam.default_grid)
    import itertools
    return [dict(zip(keys, v)) for v in itertools.product(*[fam.default_grid[k] for k in keys])]


@pytest.fixture(scope="module")
def ctx():
    panel = make_panel(5, n_sym=14, days=700)
    # heterogeneous volume so z-scores are non-degenerate
    rng = np.random.default_rng(1)
    for d in panel.values():
        d["volume"] = d["volume"] * rng.uniform(0.5, 2.0, len(d))
    bm = pd.DataFrame({s: d["close"] for s, d in panel.items()}).mean(axis=1)
    return DailyContext.from_panel(panel, bm, min_adv=5e6)


def test_all_registered_and_grids_small():
    for n in NAMES:
        fam = DAILY_FAMILIES[n]
        g = [p for p in _grid(fam) if fam.valid(p)]
        assert 1 <= len(g) <= 8, (n, len(g))


@pytest.mark.parametrize("name", NAMES)
def test_causal_deterministic_and_shape(name, ctx):
    fam = DAILY_FAMILIES[name]
    for p in _grid(fam):
        assert fam.valid(p)
        check_score_causality(fam, ctx, p, cuts=(0.6, 0.9))
    p = _grid(fam)[-1]
    a, b = fam.score(ctx, p), fam.score(ctx, p)
    pd.testing.assert_frame_equal(a, b)
    assert a.shape == ctx.close.shape and not np.isinf(a.to_numpy(float)).any()
    assert a.iloc[-1].notna().sum() > 0


@pytest.mark.parametrize("name", NAMES)
def test_short_history_is_nan_not_error(name):
    small = DailyContext.from_panel(make_panel(3, n_sym=5, days=40), None, min_adv=1.0)
    fam = DAILY_FAMILIES[name]
    for p in _grid(fam):
        s = fam.score(small, p)
        assert s.shape == small.close.shape
        if name == "xs_reversal":  # short lookback is legitimately computable after the ADV warm-up
            assert s.iloc[:19].isna().all().all()
            continue
        assert s.isna().all().all()  # not enough history for any lookback/window (or no benchmark)


def test_nan_prices_do_not_crash(ctx):
    c2 = DailyContext(ctx.open, ctx.close.mask(pd.DataFrame(np.random.default_rng(0).random(ctx.close.shape) < 0.01,
                                                           index=ctx.index, columns=ctx.symbols)),
                      ctx.volume, ctx.benchmark, ctx.cash_ret, min_adv=5e6)
    for n in NAMES:
        fam = DAILY_FAMILIES[n]
        s = fam.score(c2, _grid(fam)[0])
        assert not np.isinf(s.to_numpy(float)).any()


def test_momentum_semantics(ctx):
    fam = DAILY_FAMILIES["xs_momentum_12_1"]
    s = fam.score(ctx, {"lookback": 250, "skip": 21, "vol_scaled": 0})
    t = 400
    exp = ctx.close.iloc[t - 21] / ctx.close.iloc[t - 250] - 1
    assert np.allclose(s.iloc[t].to_numpy(float), exp.to_numpy(float))
    with pytest.raises(ValueError):
        fam.score(ctx, {"lookback": 10, "skip": 10, "vol_scaled": 0})


def test_reversal_sign_adv_filter_and_market_stop(ctx):
    fam = DAILY_FAMILIES["xs_reversal"]
    s = fam.score(ctx, {"l": 3, "min_adv_try": 0.0, "mkt_stop": 0.0})
    t = 300
    assert np.allclose(s.iloc[t], -(ctx.close.iloc[t] / ctx.close.iloc[t - 3] - 1))
    strict = fam.score(ctx, {"l": 3, "min_adv_try": 1e12, "mkt_stop": 0.0})
    assert strict.isna().all().all()
    # tiny threshold: any 20d decline of the benchmark blanks the row; rising periods stay populated
    st = fam.score(ctx, {"l": 3, "min_adv_try": 0.0, "mkt_stop": 1e-9})
    ret20 = ctx.benchmark / ctx.benchmark.shift(20) - 1
    down = (ret20 < -1e-9).to_numpy()
    assert down.any() and (~down).any()
    assert st.loc[down].isna().all().all()
    ok = (~down) & s.notna().all(axis=1).to_numpy()
    assert np.allclose(st.loc[ok].to_numpy(float), s.loc[ok].to_numpy(float))


def test_low_vol_and_low_beta_ranking():
    idx = pd.bdate_range("2020-01-01", periods=400)
    rng = np.random.default_rng(0)
    m = rng.normal(0, 0.01, 400)
    mk = lambda b, noise: 100 * np.exp(np.cumsum(b * m + rng.normal(0, noise, 400)))  # noqa: E731
    closes = pd.DataFrame({"LOW": mk(0.3, 0.002), "HIGH": mk(1.8, 0.02)}, index=idx)
    vol = pd.DataFrame(1e6, index=idx, columns=closes.columns) * rng.uniform(0.9, 1.1, (400, 2))
    bm = pd.Series(100 * np.exp(np.cumsum(m)), index=idx)
    c = DailyContext(closes, closes, vol, bm, min_adv=1.0, min_history=10)
    for name, p in (("xs_low_vol", {"window": 120}), ("xs_low_beta", {"window": 120})):
        s = DAILY_FAMILIES[name].score(c, p).iloc[-1]
        assert s["LOW"] > s["HIGH"], name
    q = DAILY_FAMILIES["xs_quality_proxy"]
    for meth in ("maxdd", "idio_vol"):
        s = q.score(c, {"method": meth, "window": 120}).iloc[-1]
        assert s["LOW"] > s["HIGH"], meth


def test_quality_proxy_without_benchmark_idio_is_nan(ctx):
    c = DailyContext(ctx.open, ctx.close, ctx.volume, None, ctx.cash_ret, min_adv=5e6)
    q = DAILY_FAMILIES["xs_quality_proxy"]
    assert q.score(c, {"method": "idio_vol", "window": 120}).isna().all().all()
    assert q.score(c, {"method": "sortino", "window": 120}).iloc[-1].notna().any()
    assert DAILY_FAMILIES["xs_low_beta"].score(c, {"window": 120}).isna().all().all()
    assert not q.valid({"method": "bogus", "window": 120})


def test_volume_shock_sign_and_invert():
    idx = pd.bdate_range("2020-01-01", periods=200)
    rng = np.random.default_rng(2)
    close = pd.DataFrame({"UP": 100.0, "DN": 100.0}, index=idx)
    vol = pd.DataFrame(rng.uniform(0.9, 1.1, (200, 2)) * 1e6, index=idx, columns=close.columns)
    close.iloc[-1] = [105.0, 95.0]
    vol.iloc[-1] = [5e6, 5e6]
    c = DailyContext(close, close, vol, None, min_adv=1.0, min_history=10)
    fam = DAILY_FAMILIES["xs_volume_shock"]
    s = fam.score(c, {"l": 1, "invert": 0}).iloc[-1]
    assert s["UP"] > 0 > s["DN"]
    s2 = fam.score(c, {"l": 1, "invert": 1}).iloc[-1]
    assert s2["UP"] < 0 < s2["DN"]
