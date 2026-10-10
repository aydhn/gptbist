import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.risk.daily_overlay import (OverlayConfig, apply_overlay, at_limit_up, dd_scale,
                                                guard_consistency, to_lots)


def _idx(n):
    return pd.bdate_range("2020-01-01", periods=n)


def _crash(n=300, seed=0):
    rng = np.random.default_rng(seed)
    r = rng.normal(0.001, 0.008, n)
    r[100:150] = -0.012  # slow crash ~ -45%
    return pd.Series(r, index=_idx(n))


def test_ladder_shape():
    c = OverlayConfig()
    assert dd_scale(0.0, c) == 1.0 and dd_scale(0.10, c) == 1.0
    assert dd_scale(0.15, c) == pytest.approx(0.25)
    assert dd_scale(0.20, c) == 0.0 and dd_scale(0.30, c) == 0.0
    assert 0.25 < dd_scale(0.125, c) < 1.0
    with pytest.raises(ValueError):
        OverlayConfig(max_dd=0.0)


def test_causality_future_does_not_change_past():
    r = _crash()
    cash = pd.Series(0.0005, index=r.index)
    reg = pd.Series(np.where(np.arange(len(r)) % 50 < 25, 1.0, 0.5), index=r.index)
    full = apply_overlay(r, reg, cash)
    k = 150
    part = apply_overlay(r.iloc[:k], reg.iloc[:k], cash.iloc[:k])
    assert np.allclose(full.exposure.iloc[:k], part.exposure)
    r2 = r.copy()
    r2.iloc[k:] = -0.05  # change the future only
    alt = apply_overlay(r2, reg, cash)
    assert np.allclose(full.exposure.iloc[:k + 1], alt.exposure.iloc[:k + 1])  # exposure at k uses data <= k-1
    assert not np.allclose(full.exposure.iloc[k + 5:], alt.exposure.iloc[k + 5:])


def test_regime_scale_uses_previous_day():
    r = pd.Series(0.0, index=_idx(10))
    reg = pd.Series(1.0, index=r.index)
    reg.iloc[4] = 0.3
    res = apply_overlay(r, reg, pd.Series(0.0, index=r.index), use_vol_target=False)
    assert res.exposure.iloc[4] == 1.0 and res.exposure.iloc[5] == pytest.approx(0.3)


def test_max_drawdown_bounded_and_cash_earns():
    r = _crash()
    cash = pd.Series(0.0008, index=r.index)
    cfg = OverlayConfig(max_dd=0.20)
    res = apply_overlay(r, None, cash, cfg, use_vol_target=False)
    raw_nav = (1 + r).cumprod()
    raw_dd = (raw_nav / raw_nav.cummax() - 1).min()
    ov = res.nav
    dd = (ov / ov.cummax() - 1).min()
    assert raw_dd < -0.25
    gap = 0.012  # one-day gap risk: exposure * worst day
    assert dd >= -(cfg.max_dd + gap)
    assert any(e["kind"] == "halt" for e in res.events)
    flat = res.exposure < 1e-12
    assert flat.any()
    assert np.allclose(res.returns[flat], cash[flat])  # fully de-risked => cash interest only


def test_hysteresis_and_reentry():
    r = _crash(400)
    cash = pd.Series(0.0004, index=r.index)
    res = apply_overlay(r, None, cash, OverlayConfig(min_halt_days=5, max_halt_days=30), use_vol_target=False)
    kinds = [e["kind"] for e in res.events]
    assert "halt" in kinds and "reenter" in kinds
    assert (res.exposure >= 0).all() and (res.exposure <= 1).all()


def test_fail_closed():
    idx = _idx(5)
    with pytest.raises(ValueError):
        apply_overlay(pd.Series([0.0, np.nan, 0, 0, 0], index=idx), None, pd.Series(0.0, index=idx))
    with pytest.raises(ValueError):
        apply_overlay(pd.Series([0.0, -1.0, 0, 0, 0], index=idx), None, pd.Series(0.0, index=idx))


def test_guard_consistency_message(settings_factory):
    s = settings_factory()
    assert guard_consistency(OverlayConfig(max_dd=0.20), s) is not None  # guard default 8% < 20%
    assert guard_consistency(OverlayConfig(max_dd=0.05), s) is None


def test_config_from_settings(settings_factory):
    c = OverlayConfig.from_settings(settings_factory())
    assert c.max_dd == 0.20 and c.floor_exposure == 0.25


# ---------------- lots
def test_to_lots_rounding_and_residual():
    w = {"A": 0.125, "B": 0.125, "C": 0.125}
    p = {"A": 33.3, "B": 101.7, "C": 7.0}
    plan = to_lots(w, p, 100_000, min_order_value=0)
    for s in w:
        assert isinstance(plan.shares[s], int)
        assert abs(plan.values[s] - 12_500) <= p[s] / 2 + 1e-6
    assert plan.residual_cash == pytest.approx(100_000 - plan.invested)
    assert plan.invested <= 100_000 * 0.375 + 1e-6
    assert plan.residual_cash >= 62_500 - 1e-6


def test_to_lots_limits_and_drops():
    w = {f"S{i}": 0.1 for i in range(10)}
    p = {f"S{i}": 10.0 for i in range(10)}
    plan = to_lots(w, p, 100_000, max_names=8)
    assert plan.n_names == 8 and sum(1 for v in plan.dropped.values() if v == "beyond_max_names") == 2
    plan = to_lots({"X": 0.6, "Y": 0.4}, {"X": 50.0, "Y": 50.0}, 100_000, per_name_cap=0.25)
    assert plan.values["X"] <= 25_050 and plan.residual_cash >= 49_900 - 1e-6
    plan = to_lots({"X": 0.001, "Y": 0.5}, {"X": 5.0, "Y": 5000.0}, 100_000, min_order_value=500)
    assert "X" in plan.dropped
    plan = to_lots({"X": 0.1, "Y": 0.1}, {"X": 5.0, "Y": 5.0}, 100_000, blocked=lambda s, p: s == "Y")
    assert plan.dropped["Y"] == "blocked_price_limit" and "Y" not in plan.shares
    plan = to_lots({"X": 0.2}, {"X": 70_000.0}, 100_000)  # not even one lot
    assert plan.shares == {} and plan.residual_cash == 100_000


def test_to_lots_fail_closed():
    with pytest.raises(ValueError):
        to_lots({"A": 0.8, "B": 0.5}, {"A": 1.0, "B": 1.0}, 1000)
    with pytest.raises(ValueError):
        to_lots({"A": -0.1}, {"A": 1.0}, 1000)
    with pytest.raises(ValueError):
        to_lots({"A": 0.1}, {"A": 1.0}, 0)


def test_to_lots_buffer_never_exceeds_capital():
    plan = to_lots({"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25}, {"A": 13.37, "B": 9.99, "C": 21.5, "D": 3.33},
                   100_000, price_buffer=0.01)
    assert plan.residual_cash >= 0


def test_at_limit_up():
    assert at_limit_up(10.0, 11.0) and not at_limit_up(10.0, 10.5)
