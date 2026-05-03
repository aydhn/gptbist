import pytest
import pandas as pd
from datetime import datetime, timezone

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.models import MarketDataFrame, Timeframe, DataVendor
from bist_signal_bot.features.multi_timeframe_features import MultiTimeframeFeatureBuilder

@pytest.fixture
def daily_mdf():
    dates = pd.date_range(start="2023-01-02", periods=30, freq="B")
    df = pd.DataFrame({
        "open": range(10, 40),
        "high": range(12, 42),
        "low": range(9, 39),
        "close": range(11, 41),
        "volume": [100] * 30
    }, index=dates)
    return MarketDataFrame(
        symbol="TEST",
        timeframe=Timeframe.DAILY,
        source=DataVendor.MOCK,
        data=df,
        fetched_at=datetime.now(timezone.utc)
    )

def test_builder_basic(daily_mdf):
    builder = MultiTimeframeFeatureBuilder(settings=Settings())
    res = builder.build_basic_mtf_features(daily_mdf, symbol="TEST")
    cols = res.output_data.columns
    assert "w_sma_20" in cols
    assert "w_rsi_14" in cols

def test_builder_advanced(daily_mdf):
    builder = MultiTimeframeFeatureBuilder(settings=Settings())
    res = builder.build_advanced_mtf_features(daily_mdf, symbol="TEST")
    cols = res.output_data.columns
    assert "w_sma_20" in cols
    assert "m_sma_10" in cols

def test_builder_full(daily_mdf):
    builder = MultiTimeframeFeatureBuilder(settings=Settings())
    res = builder.build_full_mtf_features(daily_mdf, symbol="TEST")
    cols = res.output_data.columns
    assert "w_bb_20_lower" in cols or "w_bb_20_l" in cols or "w_close" in cols
    assert "m_macd" in cols or "m_close" in cols
