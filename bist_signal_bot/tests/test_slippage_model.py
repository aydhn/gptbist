import pytest
import pandas as pd
from bist_signal_bot.execution_sim.slippage import SlippageEstimator
from bist_signal_bot.execution_sim.models import SimulatedOrderSide, LiquiditySnapshot, LiquidityStatus

def test_slippage_estimate_buy_increases_price():
    est = SlippageEstimator()
    res = est.estimate("ASELS", SimulatedOrderSide.BUY, 100.0, 10.0)
    assert res.estimated_fill_price > 100.0

def test_slippage_estimate_sell_decreases_price():
    est = SlippageEstimator()
    res = est.estimate("ASELS", SimulatedOrderSide.SELL, 100.0, 10.0)
    assert res.estimated_fill_price < 100.0

def test_slippage_fallback_insufficient_data():
    est = SlippageEstimator()
    # without passing valid liquidity / dataframe it falls back to fixed conservative
    res = est.estimate("ASELS", SimulatedOrderSide.BUY, 100.0, 10.0)
    assert res.estimated_slippage_bps > 0
