import random

import pytest

from bist_signal_bot.risk.sizing_intraday import (
    IntradaySizer, fractional_kelly, vol_target_fraction, liquidity_filter, max_order_value,
)

EQ = 1_000_000.0
BASE = dict(signal_confidence=0.7, price=100.0, equity=EQ, asset_vol_annual=0.30,
            adv_value_try=500_000_000.0, bar_value_try=50_000_000.0, spread_bps=10.0)


def _size(**kw):
    args = dict(BASE)
    settings = kw.pop("settings", {})
    args.update(kw)
    return IntradaySizer().size(settings=settings, **args)


def test_kelly_known_values():
    # p=.55, b=1 -> full 0.10; fraction 1.0, cap high
    assert fractional_kelly(0.55, 1, 1, fraction=1.0, cap=1.0) == pytest.approx(0.10)
    assert fractional_kelly(0.55, 1, 1, fraction=0.5, cap=1.0) == pytest.approx(0.05)
    assert fractional_kelly(0.55, 1, 1, fraction=0.25, cap=1.0) == pytest.approx(0.025)


def test_kelly_cap_and_no_edge():
    assert fractional_kelly(0.8, 2, 1, fraction=1.0, cap=0.10) == pytest.approx(0.10)
    assert fractional_kelly(0.5, 1, 1) == 0.0
    assert fractional_kelly(0.4, 1, 1) == 0.0
    assert fractional_kelly(1.2, 1, 1) == 0.0
    assert fractional_kelly(0.6, 0, 1) == 0.0
    assert fractional_kelly(float("nan"), 1, 1) == 0.0


def test_kelly_shrinkage_lowers_size():
    full = fractional_kelly(0.6, 1, 1, fraction=1.0, cap=1.0)
    few = fractional_kelly(0.6, 1, 1, fraction=1.0, cap=1.0, n_obs=20, prior_strength=200)
    many = fractional_kelly(0.6, 1, 1, fraction=1.0, cap=1.0, n_obs=20000, prior_strength=200)
    assert few < many < full + 1e-12
    assert fractional_kelly(0.51, 1, 1, n_obs=10, prior_strength=200) < fractional_kelly(0.51, 1, 1)


def test_vol_target():
    assert vol_target_fraction(0.30, 0.15) == pytest.approx(0.5)
    assert vol_target_fraction(0.05, 0.15) == 1.0  # capped at max leverage
    assert vol_target_fraction(0.05, 0.15, max_leverage=2.0) == pytest.approx(2.0)
    assert vol_target_fraction(0.0, 0.15) == 0.0


def test_liquidity_and_participation():
    assert liquidity_filter(10e6, 10, 5e6, 40) == (True, [])
    assert liquidity_filter(1e6, 10, 5e6, 40)[1] == ["illiquid"]
    assert liquidity_filter(10e6, 80, 5e6, 40)[1] == ["wide_spread"]
    assert max_order_value(100e6, 10e6, 0.05) == pytest.approx(0.5e6)
    assert max_order_value(1e6, 10e6, 0.05) == pytest.approx(50_000)
    assert max_order_value(1e6, 0, 0.05) == 0.0


def test_binding_vol_target_and_max_position():
    d = _size(asset_vol_annual=0.30, stop_distance=1.0)  # risk budget huge; vol .5 -> 500k; maxpos 100k
    assert d.allowed and d.method == "max_position"
    assert d.qty == 1000 and d.notional == pytest.approx(100_000)
    d = _size(asset_vol_annual=3.0, stop_distance=1.0)  # vol frac .05 -> 50k < maxpos
    assert d.method == "vol_target" and d.qty == 500


def test_binding_risk_budget():
    # 25bps of 1M = 2500 risk, stop 5 => 500 sh = 50k notional
    d = _size(stop_distance=5.0)
    assert d.method == "risk_budget" and d.qty == 500
    assert d.risk_bps == pytest.approx(25.0)
    assert "binding_constraint=risk_budget" in d.reasons


def test_binding_kelly():
    stats = dict(p_win=0.55, avg_win=1, avg_loss=1)
    d = _size(edge_stats=stats, stop_distance=1.0,
              settings={"RISK_KELLY_FRACTION": 0.25, "RISK_KELLY_CAP": 0.10})
    assert d.method == "kelly" and d.qty == 250  # 0.025 * 1M / 100


def test_binding_participation_and_gross_and_cash():
    d = _size(bar_value_try=400_000.0, stop_distance=1.0)  # 5% of 400k = 20k
    assert d.method == "participation" and d.qty == 200
    d = _size(stop_distance=1.0, open_positions=[{"symbol": "A", "notional": 950_000.0}])
    assert d.method == "gross_budget" and d.qty == 500
    d = _size(stop_distance=1.0, cash=30_000.0)
    assert d.method == "cash" and d.qty == 300


def test_lot_rounding():
    d = _size(price=33.3, stop_distance=0.01, settings={"RISK_LOT_SIZE": 100})
    assert d.allowed and d.qty % 100 == 0
    d = _size(price=33.3, stop_distance=0.01, settings={"RISK_LOT_SIZE": 1})
    assert d.qty == int(100_000 // 33.3)


def test_rejections():
    assert _size(adv_value_try=1e6).reasons == ["illiquid"]
    assert _size(spread_bps=90.0).reasons == ["wide_spread"]
    assert _size(price=0.0).reasons == ["price_outside_tick_sanity"]
    assert _size(side="SHORT").reasons == ["long_only_violation"]
    assert _size(side="SHORT", settings={"INTRADAY_ALLOW_SHORT": True}).allowed
    assert _size(settings={"RISK_KELLY_REQUIRED": True}).reasons == ["no_edge_stats"]
    assert _size(edge_stats=dict(p_win=0.45, avg_win=1, avg_loss=1)).reasons == ["no_edge"]
    assert _size(equity=50.0).reasons[0].startswith("qty_below_one_lot")
    assert not _size(equity=50.0).allowed


def test_price_limit_rejection():
    assert _size(daily_limits=(90.0, 100.1)).reasons == ["price_at_upper_limit"]
    assert _size(daily_limits=(99.95, 110.0)).reasons == ["price_at_lower_limit"]
    assert _size(daily_limits=(90.0, 110.0)).allowed


def test_property_never_exceeds_caps():
    rng = random.Random(1234)
    for _ in range(200):
        eq = rng.uniform(50_000, 5_000_000)
        price = rng.uniform(1, 800)
        adv = rng.uniform(5e6, 2e9)
        bar = rng.uniform(1e4, 1e8)
        vol = rng.uniform(0.05, 1.5)
        pos_pct = rng.uniform(0.02, 0.2)
        part = rng.uniform(0.01, 0.1)
        stats = dict(p_win=rng.uniform(0.4, 0.7), avg_win=rng.uniform(0.5, 2), avg_loss=rng.uniform(0.5, 2),
                     n_obs=rng.randint(10, 2000)) if rng.random() < 0.5 else None
        d = IntradaySizer().size(
            0.6, price, eq, vol, adv, bar, 10.0, stats, [],
            {"RISK_MAX_POSITION_PCT": pos_pct, "RISK_MAX_PARTICIPATION": part})
        assert d.qty * price <= eq * pos_pct + 1e-6
        assert d.qty * price <= part * adv + 1e-6
        assert d.qty * price <= part * bar + 1e-6
        assert d.qty >= 0 and (d.allowed == (d.qty >= 1))
