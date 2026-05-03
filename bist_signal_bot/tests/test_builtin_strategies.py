import pytest
import pandas as pd
from typing import Any

from bist_signal_bot.strategies.builtin import (
    MovingAverageTrendStrategy,
    RSIMeanReversionStrategy,
    BreakoutVolumeStrategy,
    CompositeFeatureStrategy
)
from bist_signal_bot.strategies.context import StrategyContext
from bist_signal_bot.signals.models import SignalDirection

def test_moving_average_strategy():
    strat = MovingAverageTrendStrategy()

    # Needs at least 50 rows, simulate a clear uptrend
    data = {"close": [10 + i for i in range(60)]}
    df = pd.DataFrame(data)
    ctx = StrategyContext(symbol="ASELS", data=df)

    # Run strategy
    res = strat.run(ctx)
    assert res.status == "success"
    assert res.candidate is not None
    assert res.candidate.direction == SignalDirection.LONG

def test_moving_average_strategy_short():
    strat = MovingAverageTrendStrategy()

    # Simulate a downtrend
    data = {"close": [100 - i for i in range(60)]}
    df = pd.DataFrame(data)
    ctx = StrategyContext(symbol="ASELS", data=df)

    # Run with allow_short=False (default)
    res1 = strat.run(ctx)
    # Should be WATCH or FLAT
    assert res1.candidate.direction in [SignalDirection.WATCH, SignalDirection.FLAT]

    # Run with allow_short=True
    res2 = strat.run(ctx, params={"allow_short": True})
    assert res2.candidate.direction == SignalDirection.SHORT

def test_rsi_strategy():
    strat = RSIMeanReversionStrategy()

    # Simulate big drop to force oversold
    close = [100.0] * 15 + [90.0, 80.0, 70.0, 60.0, 50.0]
    df = pd.DataFrame({"close": close})
    ctx = StrategyContext(symbol="ASELS", data=df)

    res = strat.run(ctx)
    assert res.status == "success"
    assert res.candidate is not None
    assert res.candidate.direction == SignalDirection.LONG

def test_breakout_strategy():
    strat = BreakoutVolumeStrategy()

    # Need 25 rows, recent high breakout + high volume
    high = [10.0] * 20 + [10.5, 11.0, 10.2, 10.1, 12.0]
    low = [9.0] * 25
    close = [9.5] * 20 + [10.0, 10.5, 9.8, 9.9, 11.8]
    volume = [100] * 24 + [500]  # huge volume spike on last bar

    df = pd.DataFrame({"high": high, "low": low, "close": close, "volume": volume})
    ctx = StrategyContext(symbol="ASELS", data=df)

    res = strat.run(ctx, params={"price_window": 10, "volume_window": 10})
    assert res.status == "success"
    assert res.candidate is not None
    assert res.candidate.direction == SignalDirection.LONG

def test_composite_strategy():
    strat = CompositeFeatureStrategy()

    # Mocking features directly
    df = pd.DataFrame({
        "close": [100.0],
        "trend_score": [80.0],
        "momentum_score": [75.0],
        "volume_score": [90.0]
    })
    ctx = StrategyContext(symbol="ASELS", data=df)

    res = strat.run(ctx)
    assert res.status == "success"
    assert res.candidate is not None
    assert res.candidate.direction == SignalDirection.LONG
