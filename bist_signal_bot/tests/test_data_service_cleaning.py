import pytest
from datetime import datetime, UTC
import pandas as pd
import numpy as np

from bist_signal_bot.data.data_service import MarketDataService, MarketDataServiceConfig
from bist_signal_bot.data.mock_provider import MockMarketDataProvider
from bist_signal_bot.data.cleaning import MarketDataCleaner
from bist_signal_bot.data.models import Timeframe
from bist_signal_bot.core.exceptions import DataCleaningError

@pytest.fixture
def service_with_cleaner():
    provider = MockMarketDataProvider(rows=50)
    cleaner = MarketDataCleaner(min_rows_after_cleaning=10)
    return MarketDataService(provider=provider, cleaner=cleaner, config=MarketDataServiceConfig(clean_data=True))

def test_service_cleans_data(service_with_cleaner):
    mdf = service_with_cleaner.get_ohlcv("ASELS", Timeframe.DAILY)

    assert mdf.metadata.get("cleaned") is True
    assert mdf.metadata.get("cleaning_status") == "SUCCESS"

    report = service_with_cleaner.get_last_cleaning_report("ASELS")
    assert report is not None
    assert report.output_rows > 0

def test_service_fails_on_cleaning_error():
    # Make mock provider return bad data
    class BadProvider(MockMarketDataProvider):
        def fetch_one(self, symbol, timeframe, period=None):
            mdf = super().fetch_one(symbol, timeframe, period)
            # Add NaN to make it fail
            mdf.data.iloc[0, 0] = np.nan
            return mdf

    provider = BadProvider(rows=50)
    cleaner = MarketDataCleaner(missing_value_policy="FAIL") # Will raise
    service = MarketDataService(provider=provider, cleaner=cleaner, config=MarketDataServiceConfig(clean_data=True, fail_on_cleaning_error=True))

    with pytest.raises(DataCleaningError):
        service.get_ohlcv("ASELS", Timeframe.DAILY)
