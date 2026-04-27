from datetime import datetime

import pandas as pd
import pytest

from bist_signal_bot.core.exceptions import DataQualityError
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.data.mock_provider import MockMarketDataProvider
from bist_signal_bot.data.models import MarketDataFrame, Timeframe
from bist_signal_bot.data.quality import DataQualityChecker


@pytest.fixture
def clean_provider():
    return MockMarketDataProvider(rows=50)

@pytest.fixture
def bad_provider():
    class BadProvider(MockMarketDataProvider):
        def fetch_one(self, symbol, timeframe, period):
            dates = pd.date_range("2023-01-01", periods=10, tz="Europe/Istanbul")
            df = pd.DataFrame({
                "open": [10.0] * 10,
                "high": [12.0] * 10,
                "low": [9.0] * 10,
                "close": [11.0] * 10,
                "volume": [1000] * 10
            }, index=dates)

            # Create duplicate index to cause DataQualityError
            date_list = list(df.index)
            date_list[1] = date_list[0]
            df.index = pd.DatetimeIndex(date_list)

            mdf = MarketDataFrame(
                symbol=symbol,
                timeframe=timeframe,
                source=self.vendor,
                data=df,
                fetched_at=datetime.utcnow()
            )
            return mdf

    return BadProvider()

def test_data_service_generates_quality_report(clean_provider):
    checker = DataQualityChecker(min_rows=10)
    service = MarketDataService(provider=clean_provider, quality_checker=checker, validate_quality=True)

    mdf = service.get_ohlcv("ASELS", Timeframe.DAILY)
    assert mdf.quality_report is not None
    assert mdf.quality_report.passed is True
    assert mdf.quality_report.score == 100.0

    report = service.get_last_quality_report("ASELS")
    assert report is not None
    assert report.passed is True

def test_data_service_fail_on_quality_error(bad_provider):
    checker = DataQualityChecker(min_rows=5)
    service = MarketDataService(
        provider=bad_provider,
        quality_checker=checker,
        validate_quality=True,
        fail_on_quality_error=True
    )

    with pytest.raises(DataQualityError):
        service.get_ohlcv("ASELS", Timeframe.DAILY)
