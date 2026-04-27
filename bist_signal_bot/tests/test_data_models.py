from datetime import UTC, datetime

import pandas as pd
import pytest

from bist_signal_bot.core.exceptions import DataProviderValidationError
from bist_signal_bot.data.models import (
    DataFetchRequest,
    DataVendor,
    MarketDataFrame,
    OHLCVBar,
    Timeframe,
)


def test_timeframe_enum():
    assert Timeframe.DAILY == "1d"
    assert Timeframe.WEEKLY == "1wk"
    assert Timeframe.MONTHLY == "1mo"
    assert Timeframe.HOURLY == "1h"
    assert Timeframe.FIFTEEN_MIN == "15m"
    assert Timeframe.FIVE_MIN == "5m"

def test_ohlcv_bar_valid():
    bar = OHLCVBar(
        timestamp=datetime(2023, 1, 1, tzinfo=UTC),
        open=100.0,
        high=110.0,
        low=90.0,
        close=105.0,
        volume=1000,
        symbol="ASELS",
        timeframe=Timeframe.DAILY,
        source=DataVendor.INTERNAL
    )
    assert bar.symbol == "ASELS"
    assert bar.high >= bar.low

def test_ohlcv_bar_negative_price():
    with pytest.raises(ValueError, match="open cannot be negative"):
        OHLCVBar(
            timestamp=datetime(2023, 1, 1, tzinfo=UTC),
            open=-10.0,
            high=110.0,
            low=90.0,
            close=105.0,
            volume=1000,
            symbol="ASELS",
            timeframe=Timeframe.DAILY,
            source=DataVendor.INTERNAL
        )

def test_ohlcv_bar_high_less_than_low():
    with pytest.raises(ValueError, match="high cannot be less than low"):
        OHLCVBar(
            timestamp=datetime(2023, 1, 1, tzinfo=UTC),
            open=100.0,
            high=90.0,
            low=110.0,
            close=105.0,
            volume=1000,
            symbol="ASELS",
            timeframe=Timeframe.DAILY,
            source=DataVendor.INTERNAL
        )

def test_market_dataframe_normalization():
    df = pd.DataFrame({
        "Open": [100.0],
        "High": [110.0],
        "Low": [90.0],
        "Close": [105.0],
        "Volume": [1000]
    })

    mdf = MarketDataFrame(
        symbol="ASELS",
        timeframe=Timeframe.DAILY,
        source=DataVendor.INTERNAL,
        data=df,
        fetched_at=datetime.now(UTC)
    )
    mdf.validate_schema()
    assert list(mdf.data.columns) == ["open", "high", "low", "close", "volume"]

def test_market_dataframe_missing_columns():
    df = pd.DataFrame({
        "open": [100.0],
        "close": [105.0]
    })
    mdf = MarketDataFrame(
        symbol="ASELS",
        timeframe=Timeframe.DAILY,
        source=DataVendor.INTERNAL,
        data=df,
        fetched_at=datetime.now(UTC)
    )
    with pytest.raises(DataProviderValidationError, match="Missing required columns"):
        mdf.validate_schema()

def test_market_dataframe_non_numeric():
    df = pd.DataFrame({
        "open": ["100.0"],
        "high": [110.0],
        "low": [90.0],
        "close": [105.0],
        "volume": [1000]
    })
    mdf = MarketDataFrame(
        symbol="ASELS",
        timeframe=Timeframe.DAILY,
        source=DataVendor.INTERNAL,
        data=df,
        fetched_at=datetime.now(UTC)
    )
    with pytest.raises(DataProviderValidationError, match="must be numeric"):
        mdf.validate_schema()

def test_data_fetch_request_normalization():
    req = DataFetchRequest(
        symbols=["asels.is", "THYAO"],
        timeframe=Timeframe.DAILY
    )
    assert req.symbols == ["ASELS", "THYAO"]
