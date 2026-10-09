import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.edge_validation.labels import forward_return_labels, triple_barrier_labels

TZ = "Europe/Istanbul"


def make_bars(days=3, per_day=10, seed=0):
    rng = np.random.default_rng(seed)
    idx = []
    for d in pd.bdate_range("2024-03-04", periods=days):
        idx += list(pd.date_range(d + pd.Timedelta(hours=10), periods=per_day, freq="10min", tz=TZ))
    idx = pd.DatetimeIndex(idx)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.003, len(idx))))
    open_ = np.r_[close[0], close[:-1]] * (1 + rng.normal(0, 0.0005, len(idx)))
    high = np.maximum(open_, close) * 1.0005
    low = np.minimum(open_, close) * 0.9995
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close,
                         "volume": 1000.0}, index=idx)


def day_of(ts):
    return ts.tz_convert(TZ).date()


def test_session_bound_never_crosses_day_and_next_bar_entry():
    bars = make_bars()
    lab = forward_return_labels(bars, horizon_bars=4, session_bound=True)
    assert len(lab) > 0
    assert all(day_of(a) == day_of(b) for a, b in zip(lab.t0, lab.t1))
    # last bar of each day has no next bar in session -> dropped
    last_bars = bars.groupby(bars.index.date).tail(1).index
    assert not set(last_bars) & set(lab.t0)
    pos = bars.index.get_loc
    for _, r in lab.iterrows():
        e = pos(r.t0) + 1
        assert r.ret == pytest.approx(bars["close"].iloc[pos(r.t1)] / bars["open"].iloc[e] - 1)
        assert pos(r.t1) >= e
    # horizon truncated at session end: second-to-last bar exits at day's last bar
    row = lab[lab.t0 == bars.index[8]].iloc[0]
    assert row.t1 == bars.index[9]


def test_not_session_bound_crosses_and_drops_tail():
    bars = make_bars()
    lab = forward_return_labels(bars, horizon_bars=4, session_bound=False)
    assert any(day_of(a) != day_of(b) for a, b in zip(lab.t0, lab.t1))
    assert lab.t0.max() == bars.index[-5]


def test_fee_reduces_return():
    bars = make_bars()
    a = forward_return_labels(bars, 3)
    b = forward_return_labels(bars, 3, fee_bps=10)
    assert np.allclose(a.ret - b.ret, 2 * 10 / 1e4)


def test_no_lookahead_beyond_t1():
    bars = make_bars()
    lab = forward_return_labels(bars, horizon_bars=3)
    row = lab.iloc[2]
    mod = bars.copy()
    mod.loc[mod.index > row.t1, ["open", "high", "low", "close"]] *= 7.0
    lab2 = forward_return_labels(mod, horizon_bars=3)
    r2 = lab2[lab2.t0 == row.t0].iloc[0]
    assert r2.ret == pytest.approx(row.ret) and r2.t1 == row.t1 and r2.label == row.label


def _tb_setup():
    bars = make_bars(days=2, per_day=12, seed=3)
    # tighten bar ranges so barriers are not hit accidentally
    bars["high"] = bars[["open", "close"]].max(axis=1)
    bars["low"] = bars[["open", "close"]].min(axis=1)
    return bars


def test_triple_barrier_profit_stop_vertical():
    bars = _tb_setup()
    W, H, i = 4, 5, 6
    base = triple_barrier_labels(bars, 2.0, 2.0, W, H)
    vol = base[base.t0 == bars.index[i]].vol.iloc[0]
    p = bars["open"].iloc[i + 1]
    # profit target on bar i+3
    up = bars.copy()
    up.iloc[i + 3, up.columns.get_loc("high")] = p * (1 + 2.0 * vol) * 1.001
    r = triple_barrier_labels(up, 2.0, 2.0, W, H)
    r = r[r.t0 == bars.index[i]].iloc[0]
    assert (r.label, r.barrier, r.t1) == (1, "pt", bars.index[i + 3])
    assert r.ret == pytest.approx(2.0 * vol)
    # stop loss on bar i+2
    dn = bars.copy()
    dn.iloc[i + 2, dn.columns.get_loc("low")] = p * (1 - 2.0 * vol) * 0.999
    r = triple_barrier_labels(dn, 2.0, 2.0, W, H)
    r = r[r.t0 == bars.index[i]].iloc[0]
    assert (r.label, r.barrier, r.t1) == (-1, "sl", bars.index[i + 2])
    assert r.ret == pytest.approx(-2.0 * vol)
    # both touched in the same bar -> stop first
    both = up.copy()
    both.iloc[i + 3, both.columns.get_loc("low")] = p * (1 - 2.0 * vol) * 0.999
    r = triple_barrier_labels(both, 2.0, 2.0, W, H)
    assert r[r.t0 == bars.index[i]].iloc[0].label == -1
    # huge barriers -> vertical at i+H
    v = triple_barrier_labels(bars, 1000.0, 1000.0, W, H)
    r = v[v.t0 == bars.index[i]].iloc[0]
    assert (r.label, r.barrier, r.t1) == (0, "vertical", bars.index[i + H])


def test_triple_barrier_session_bound_and_no_lookahead():
    bars = _tb_setup()
    tb = triple_barrier_labels(bars, 1000.0, 1000.0, 4, 8)
    assert all(day_of(a) == day_of(b) for a, b in zip(tb.t0, tb.t1))
    r = tb[tb.t0 == bars.index[9]].iloc[0]  # day of 12 bars: horizon truncated at bar 11
    assert r.t1 == bars.index[11]
    tb2 = triple_barrier_labels(bars, 2.0, 2.0, 4, 3)
    row = tb2.iloc[3]
    mod = bars.copy()
    mod.loc[mod.index > row.t1, ["open", "high", "low", "close"]] *= 5.0
    t3 = triple_barrier_labels(mod, 2.0, 2.0, 4, 3)
    r3 = t3[t3.t0 == row.t0].iloc[0]
    assert (r3.t1, r3.label) == (row.t1, row.label) and r3.ret == pytest.approx(row.ret)
