import math

import pandas as pd
import pytest

from bist_signal_bot.edge_validation.costs import IntradayCostModel, liquidity_ok, tick_size


def test_tick_bands():
    assert tick_size(10) == 0.01
    assert tick_size(30) == 0.02
    assert tick_size(50) == 0.05
    assert tick_size(150) == 0.10


def test_cost_hand_computed():
    m = IntradayCostModel()
    b = m.breakdown(50.0, 10_000, 1_000_000, "buy")
    assert b.commission_bps == 5.0
    assert b.bsmv_bps == pytest.approx(0.25)          # BSMV on commission only
    assert b.exchange_bps == 0.3
    assert b.half_spread_bps == pytest.approx(5.0)    # 0.5*0.05/50*1e4
    assert b.impact_bps == pytest.approx(1.0)         # 0.1*sqrt(0.01)*100
    assert m.cost_bps(50.0, 10_000, 1_000_000) == pytest.approx(11.55)
    assert m.round_trip_bps(50.0, 10_000, 1_000_000) == pytest.approx(23.1)


def test_participation_cap_and_short():
    m = IntradayCostModel()
    assert math.isnan(m.cost_bps(50.0, 100_000, 1_000_000))
    assert m.breakdown(50.0, 100_000, 1_000_000).reason == "participation_cap"
    assert math.isnan(m.cost_bps(50.0, 1000, 1_000_000, "short"))
    assert not math.isnan(IntradayCostModel(allow_short=True).cost_bps(50.0, 1000, 1_000_000, "short"))
    assert math.isnan(m.cost_bps(50.0, 1000, 0))


def test_apply_costs_vectorized():
    m = IntradayCostModel()
    g = pd.Series([0.01, 0.02, 0.03], index=list("abc"))
    net = m.apply_costs(g, 50.0, [10_000, 10_000, 100_000], 1_000_000)
    assert isinstance(net, pd.Series)
    assert net["a"] == pytest.approx(0.01 - 23.1e-4)
    assert math.isnan(net["c"])


def test_from_settings_and_liquidity():
    m = IntradayCostModel.from_settings()
    assert m.commission_bps == 5.0 and m.allow_short is False and m.max_participation == 0.05
    assert liquidity_ok(5e6, 1e6) and not liquidity_ok(5e5, 1e6) and not liquidity_ok(float("nan"), 1)
