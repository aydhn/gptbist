import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.edge_validation.labels_daily import (
    forward_return_labels_daily,
    meta_labels,
    triple_barrier_labels_daily,
)


def _bars(n=80, seed=1, tz=None):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2023-01-02", periods=n, tz=tz)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    op = close * (1 + rng.normal(0, 0.002, n))
    hi = np.maximum(op, close) * (1 + np.abs(rng.normal(0, 0.004, n)))
    lo = np.minimum(op, close) * (1 - np.abs(rng.normal(0, 0.004, n)))
    return pd.DataFrame({"open": op, "high": hi, "low": lo, "close": close,
                         "volume": rng.integers(1000, 5000, n)}, index=idx)


def test_forward_hand_example():
    idx = pd.bdate_range("2024-01-01", periods=5)
    b = pd.DataFrame({"open": [10, 11, 12, 13, 14.0], "high": 20.0, "low": 1.0,
                      "close": [10.5, 11.5, 12.5, 13.5, 14.5], "volume": 1}, index=idx)
    out = forward_return_labels_daily(b, 2)
    assert len(out) == 3  # t0 = day0..day2; exit = t0+2 <= day4
    assert out.loc[0, "t_entry"] == idx[1] and out.loc[0, "t1"] == idx[2]
    assert out.loc[0, "ret"] == pytest.approx(12.5 / 11 - 1)
    assert out.loc[0, "entry_price"] == 11
    assert out.loc[2, "t1"] == idx[4]
    fee = forward_return_labels_daily(b, 2, fee_bps=10)
    assert fee.loc[0, "ret"] == pytest.approx(12.5 / 11 - 1 - 0.002)
    close_entry = forward_return_labels_daily(b, 2, entry="close")
    assert close_entry.loc[0, "ret"] == pytest.approx(12.5 / 10.5 - 1)


def test_forward_no_lookahead_and_drop():
    b = _bars()
    full = forward_return_labels_daily(b, 5)
    assert len(full) == len(b) - 5
    assert full["t1"].max() == b.index[-1]
    cut = forward_return_labels_daily(b.iloc[:50], 5)
    pd.testing.assert_frame_equal(full.iloc[: len(cut)], cut)
    b2 = b.copy()
    b2.iloc[60:, :4] *= 3.0  # change future bars
    ch = forward_return_labels_daily(b2, 5)
    done = full[full["t1"] < b.index[60]]
    pd.testing.assert_frame_equal(ch.iloc[: len(done)], done)


def test_forward_edge_cases():
    b = _bars(3)
    assert forward_return_labels_daily(b, 5).empty
    assert forward_return_labels_daily(b.iloc[:1], 1).empty
    with pytest.raises(ValueError):
        forward_return_labels_daily(b, 0)
    b = _bars(10)
    b.iloc[4, b.columns.get_loc("open")] = np.nan
    out = forward_return_labels_daily(b, 2)
    assert np.isfinite(out["ret"]).all()
    assert b.index[4] not in set(out["t_entry"])
    z = _bars(10)
    z["volume"] = 0
    assert len(forward_return_labels_daily(z, 2)) == 8


def test_forward_tz_aware():
    b = _bars(20, tz="Europe/Istanbul")
    out = forward_return_labels_daily(b, 3)
    assert out["t0"].dt.tz is not None and len(out) == 17


def _tb_brute(b, i, pt_mult, sl_mult, h, vol):
    entry = b["open"].iloc[i + 1]
    pt, sl = entry * (1 + pt_mult * vol), entry * (1 - sl_mult * vol)
    for k in range(i + 1, i + h + 1):
        if b["low"].iloc[k] <= sl:
            return "sl", k, sl / entry - 1
        if b["high"].iloc[k] >= pt:
            return "pt", k, pt / entry - 1
    return "vertical", i + h, b["close"].iloc[i + h] / entry - 1


def test_triple_barrier_matches_bruteforce():
    b = _bars(150, seed=3)
    vw, h = 10, 6
    out = triple_barrier_labels_daily(b, 1.5, 1.0, vw, h)
    vol = np.log(b["close"]).diff().ewm(span=vw, min_periods=vw).std()
    assert len(out) > 50
    assert set(out["barrier"]) <= {"pt", "sl", "vertical"}
    for _, r in out.iterrows():
        i = b.index.get_loc(r["t0"])
        bar, k, ret = _tb_brute(b, i, 1.5, 1.0, h, vol.iloc[i])
        assert r["barrier"] == bar and r["t1"] == b.index[k]
        assert r["ret"] == pytest.approx(ret)
        assert r["label"] == {"pt": 1, "sl": -1, "vertical": 0}[bar]
        assert r["t_entry"] == b.index[i + 1]


def test_triple_barrier_stop_first_on_tie_and_fee():
    b = _bars(60, seed=4)
    p = 40
    b.iloc[p, b.columns.get_loc("high")] = 1e6
    b.iloc[p, b.columns.get_loc("low")] = 1e-6
    out = triple_barrier_labels_daily(b, 1.0, 1.0, 10, 5)
    row = out[out["t0"] == b.index[p - 1]].iloc[0]
    assert row["barrier"] == "sl" and row["t1"] == b.index[p] and row["label"] == -1
    fee = triple_barrier_labels_daily(b, 1.0, 1.0, 10, 5, fee_bps=10)
    row2 = fee[fee["t0"] == b.index[p - 1]].iloc[0]
    assert row2["ret"] == pytest.approx(row["ret"] - 0.002)


def test_triple_barrier_no_lookahead():
    b = _bars(120, seed=5)
    full = triple_barrier_labels_daily(b, 2, 1, 10, 5)
    cut = triple_barrier_labels_daily(b.iloc[:80], 2, 1, 10, 5)
    pd.testing.assert_frame_equal(full.iloc[: len(cut)], cut)
    b2 = b.copy()
    b2.iloc[90:, :4] *= 0.2
    ch = triple_barrier_labels_daily(b2, 2, 1, 10, 5)
    done = full[full["t1"] < b.index[90]]
    assert len(done) > 0
    pd.testing.assert_frame_equal(ch.iloc[: len(done)], done)
    assert full["t1"].max() <= b.index[-1]


def test_triple_barrier_edge_cases():
    assert triple_barrier_labels_daily(_bars(4), 1, 1, 10, 5).empty
    b = _bars(60)
    b.iloc[20, b.columns.get_loc("close")] = np.nan
    out = triple_barrier_labels_daily(b, 1, 1, 5, 3)
    assert np.isfinite(out["ret"]).all()
    z = b.copy()
    z["volume"] = 0
    assert len(triple_barrier_labels_daily(z, 1, 1, 5, 3)) > 0
    with pytest.raises(ValueError):
        triple_barrier_labels_daily(b, 0, 1, 5, 3)


def test_meta_labels():
    b = _bars(100, seed=6)
    tb = triple_barrier_labels_daily(b, 1.0, 1.0, 10, 5)
    sig = pd.Series(False, index=b.index)
    sig.iloc[[30, 40, 50]] = True
    m = meta_labels(sig, tb)
    assert set(m["t0"]) == set(b.index[[30, 40, 50]]) & set(tb["t0"])
    assert len(m) == 3
    exp = (tb.set_index("t0").loc[m["t0"], "ret"].to_numpy() > 0).astype(int)
    assert (m["meta_label"].to_numpy() == exp).all()
    assert meta_labels(sig & False, tb).empty
    sig_tz = sig.copy()
    sig_tz.index = sig_tz.index.tz_localize("Europe/Istanbul")
    assert len(meta_labels(sig_tz, tb)) == len(m)
