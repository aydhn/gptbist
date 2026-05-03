import pytest
import pandas as pd
from datetime import datetime, timezone

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.models import MarketDataFrame, Timeframe, DataVendor
from bist_signal_bot.timeframes.engine import MultiTimeframeEngine

@pytest.fixture
def daily_mdf():
    dates = pd.date_range(start="2023-01-02", periods=20, freq="B")
    df = pd.DataFrame({
        "open": range(10, 30),
        "high": range(12, 32),
        "low": range(9, 29),
        "close": range(11, 31),
        "volume": [100] * 20
    }, index=dates)
    return MarketDataFrame(
        symbol="TEST",
        timeframe=Timeframe.DAILY,
        source=DataVendor.MOCK,
        data=df,
        fetched_at=datetime.now(timezone.utc)
    )

def test_engine_build_from_base_data(daily_mdf):
    settings = Settings()
    engine = MultiTimeframeEngine(settings=settings)

    res = engine.build_from_base_data(daily_mdf, higher_timeframes=[Timeframe.WEEKLY])

    assert res.symbol == "TEST"
    assert res.base_timeframe == "1d"
    assert "w_close" in res.output_data.columns
    # Ensure indicator columns exist based on defaults (sma_20, etc.)
    # Since we only gave 20 days, 20 week SMA will be NaN but column should exist.
    assert "w_sma_20" in res.output_data.columns
