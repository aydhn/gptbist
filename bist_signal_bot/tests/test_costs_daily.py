import math

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.costs_daily import DailyCostModel
from bist_signal_bot.edge_validation.gate import CandidateGate


def _m(c):
    return DailyCostModel(commission_bps=c)


def test_scenarios_differ_exactly_by_commission_legs():
    z, p = _m(0.0), _m(5.0)
    d = p.cost_bps(50.0, 1e5, 1e8) - z.cost_bps(50.0, 1e5, 1e8)
    assert math.isclose(d, 5.0 * 1.05)  # commission + BSMV on commission
    rt = p.round_trip_bps(50.0, 1e5, 1e8) - z.round_trip_bps(50.0, 1e5, 1e8)
    assert math.isclose(rt, 2 * 5.0 * 1.05)
    assert z.breakdown(50.0, 1e5, 1e8).bsmv_bps == 0.0


def test_from_settings_scenarios():
    class S:
        DAILY_COST_COMMISSION_PLACEHOLDER_BPS = 5.0
        DAILY_COST_BSMV_RATE = 0.05
        DAILY_COST_EXCHANGE_FEE_BPS = 0.3
        DAILY_COST_IMPACT_COEF = 0.5
        DAILY_COST_MAX_PARTICIPATION = 0.05
        CASH_BENCHMARK_ANNUAL_RATE = 0.37
        CASH_BENCHMARK_WITHHOLDING = 0.0

    assert DailyCostModel.from_settings(S, "zero_commission").commission_bps == 0.0
    assert DailyCostModel.from_settings(S, "placeholder_commission").commission_bps == 5.0


def test_real_settings_have_keys():
    z = DailyCostModel.from_settings(None, "zero_commission")
    assert z.cash_annual_rate == 0.37 and z.commission_bps == 0.0


def test_monotonic_in_participation_and_nan_illiquid():
    m = _m(0.0)
    c = [m.cost_bps(50.0, v, 1e8) for v in (1e5, 1e6, 4e6)]
    assert c[0] < c[1] < c[2]
    assert math.isnan(m.cost_bps(50.0, 6e6, 1e8))  # 6% > 5%
    assert math.isnan(m.cost_bps(50.0, 1e5, 0.0))
    assert math.isnan(m.cost_bps(50.0, 1e5, 1e8, at_price_limit=True))
    assert math.isnan(m.cost_bps(50.0, 1e5, 1e8, side="short"))
    out = m.apply_costs(np.array([0.01, 0.01]), 50.0, np.array([1e5, 6e6]), 1e8)
    assert np.isfinite(out[0]) and np.isnan(out[1])


def test_holding_cost_and_net_vs_cash():
    m = DailyCostModel(cash_annual_rate=0.37, cash_withholding=0.0)
    assert math.isclose(m.holding_cost_bps(365), 0.37 * 1e4)
    assert math.isclose(m.holding_cost_bps(365, withholding=0.15), 0.37 * 0.85 * 1e4)
    assert m.holding_cost_bps(0) == 0.0
    assert math.isclose(m.net_vs_cash(0.10, 365), 0.10 - 0.37)


def test_gate_net_compat():
    ev = pd.DataFrame({"gross_ret": [0.02, 0.01], "price": [50.0, 50.0], "order_value": [1e5, 9e6],
                       "bar_value_try": [1e8, 1e8]})
    gate = CandidateGate(cost_model=_m(5.0), save=False)
    out = CandidateGate._net(gate, ev)
    assert out["net_ret"].iloc[0] < 0.02 and np.isnan(out["net_ret"].iloc[1])
