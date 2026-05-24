import pytest
import pandas as pd
from datetime import datetime
from bist_signal_bot.execution_sim.liquidity import LiquidityAnalyzer
from bist_signal_bot.execution_sim.models import LiquidityStatus

def test_liquidity_insufficient_data():
    analyzer = LiquidityAnalyzer()
    snapshot = analyzer.analyze("ASELS", pd.DataFrame())
    assert snapshot.status == LiquidityStatus.INSUFFICIENT_DATA

def test_liquidity_turnover_calculation():
    analyzer = LiquidityAnalyzer()
    df = pd.DataFrame({"close": [10.0, 10.0], "volume": [1000, 1000]})
    snapshot = analyzer.analyze("ASELS", df, requested_notional=5000)
    assert snapshot.average_turnover == 10000.0
    # 50% participation -> ILLIQUID (based on default 10% threshold)
    assert snapshot.status == LiquidityStatus.ILLIQUID
