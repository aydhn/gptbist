import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.edge_validation.regime_labels import (
    REGIMES,
    breadth_regime,
    label_regimes,
    regime_exposure_scale,
)


def _idx_close(n=700, seed=0):
    rng = np.random.default_rng(seed)
    vol = np.where((np.arange(n) // 120) % 2 == 0, 0.006, 0.02)
    r = rng.normal(0.0003, vol)
    return pd.Series(1000 * np.exp(np.cumsum(r)), index=pd.bdate_range("2020-01-01", periods=n))


def test_label_regimes_shape_and_values():
    df = label_regimes(_idx_close())
    assert list(df.columns) == ["date", "trend", "vol", "regime", "exposure_scale"]
    assert set(df["regime"]) <= set(REGIMES)
    assert set(df["trend"]) <= {"bull", "bear", "neutral"}
    assert set(df["vol"]) <= {"low", "high"}
    assert ((df["exposure_scale"] > 0) & (df["exposure_scale"] <= 1)).all()
    assert 0 < len(df) < 700  # warm-up dropped
    assert df["vol"].nunique() == 2


def test_label_regimes_causal_prefix():
    s = _idx_close()
    full = label_regimes(s)
    cut = label_regimes(s.iloc[:500])
    pd.testing.assert_frame_equal(full.iloc[: len(cut)].reset_index(drop=True), cut)
    s2 = s.copy()
    s2.iloc[550:] *= 0.3  # change the future
    ch = label_regimes(s2)
    k = int((full["date"] < s.index[550]).sum())
    assert k > 0
    pd.testing.assert_frame_equal(ch.iloc[:k], full.iloc[:k])


def test_label_regimes_trend_directions():
    base = np.linspace(100, 300, 400) * (1 + 0.001 * np.sin(np.arange(400)))
    idx = pd.bdate_range("2020-01-01", periods=400)
    assert (label_regimes(pd.Series(base, index=idx))["trend"] == "bull").all()
    assert (label_regimes(pd.Series(base[::-1], index=idx))["trend"] == "bear").all()


def test_label_regimes_edge_cases():
    assert label_regimes(pd.Series(dtype=float)).empty
    short = pd.Series([1.0, 2, 3], index=pd.bdate_range("2020-01-01", periods=3))
    assert label_regimes(short).empty
    s = _idx_close()
    s.iloc[300] = np.nan
    d = label_regimes(s)
    assert d["exposure_scale"].notna().all()


def test_exposure_scale_rule():
    df = pd.DataFrame({"trend": ["bull", "bull", "bear", "bear"],
                       "vol": ["low", "high", "low", "high"]})
    sc = regime_exposure_scale(df, bear_scale=0.4, volatile_scale=0.6)
    assert sc.tolist() == pytest.approx([1.0, 0.6, 0.4, 0.24])
    with pytest.raises(ValueError):
        regime_exposure_scale(df, bear_scale=0.0)
    df.index = pd.bdate_range("2024-01-01", periods=4)
    br = pd.Series([0.5, 0.5, 0.0, 0.25], index=df.index)
    sc2 = regime_exposure_scale(df, breadth=br, breadth_floor=0.5)
    assert sc2.iloc[0] == 1.0
    assert sc2.iloc[2] == pytest.approx(0.4 * 0.5)
    assert sc2.iloc[3] == pytest.approx(0.24 * 0.75)
    assert (sc2 <= 1).all() and (sc2 > 0).all()


def test_breadth_regime():
    n = 260
    idx = pd.bdate_range("2020-01-01", periods=n)
    up = pd.DataFrame({f"U{i}": np.linspace(10, 20, n) for i in range(3)}, index=idx)
    dn = pd.DataFrame({"D0": np.linspace(20, 10, n)}, index=idx)
    m = pd.concat([up, dn], axis=1)
    b = breadth_regime(m)
    assert b["pct_above_long"].iloc[-1] == pytest.approx(0.75)
    assert b["breadth"].iloc[-1] == "strong"
    assert len(b) == n - 199
    cut = breadth_regime(m.iloc[:230])
    pd.testing.assert_frame_equal(b.iloc[: len(cut)], cut)
    m2 = m.copy()
    m2["N"] = np.nan
    assert breadth_regime(m2)["pct_above_long"].iloc[-1] == pytest.approx(0.75)
    assert breadth_regime(pd.DataFrame()).empty
