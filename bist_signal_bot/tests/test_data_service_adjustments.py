from datetime import datetime, UTC
import pandas as pd
import pytest

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.adjustments import PriceAdjustmentEngine
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.data.mock_provider import MockMarketDataProvider
from bist_signal_bot.data.models import AdjustmentPolicy, Timeframe, MarketDataFrame, DataVendor

def test_data_service_adjustment_integration():
    settings = Settings(ENABLE_PRICE_ADJUSTMENTS=True)
    provider = MockMarketDataProvider(rows=252)

    # We create an engine that uses USE_PROVIDER_ADJUSTED
    engine = PriceAdjustmentEngine(policy=AdjustmentPolicy.USE_PROVIDER_ADJUSTED, strict=False)

    service = MarketDataService(
        provider=provider,
        prefer_local=False,
        clean_data=False,
        validate_quality=False,
        apply_price_adjustments=True,
        adjustment_engine=engine
    )

    # Let's intercept the mock provider to return data with adj_close
    original_fetch = provider.fetch_one
    def mock_fetch_one(symbol, timeframe, period="2y"):
        mdf = original_fetch(symbol, timeframe, period)
        # Add adj_close 50% of close
        mdf.data["adj_close"] = mdf.data["close"] * 0.5
        return mdf

    provider.fetch_one = mock_fetch_one

    mdf = service.get_ohlcv("ASELS", timeframe=Timeframe.DAILY, refresh=True, save=False)

    report = service.get_last_adjustment_report("ASELS")
    assert report is not None
    assert report.policy == AdjustmentPolicy.USE_PROVIDER_ADJUSTED

    # Ensure it's adjusted (price should be 0.5 of original, original is 10 for mock data usually, wait, mock_fetch generates random data)
    # Actually mock_fetch_one does Brownian motion. But `adj_close` was 0.5 * close, so the factor applied is 0.5.
    # We can just check the metadata.
    assert mdf.metadata.get("adjusted_by_engine") is True
    assert mdf.metadata.get("actions_applied", 0) == 1

def test_data_service_skips_when_disabled():
    settings = Settings(ENABLE_PRICE_ADJUSTMENTS=False)
    provider = MockMarketDataProvider(rows=252)

    engine = PriceAdjustmentEngine(policy=AdjustmentPolicy.MANUAL_SPLIT_ADJUST)

    service = MarketDataService(
        provider=provider,
        prefer_local=False,
        clean_data=False,
        validate_quality=False,
        apply_price_adjustments=False,  # disabled!
        adjustment_engine=engine
    )

    mdf = service.get_ohlcv("ASELS", timeframe=Timeframe.DAILY, refresh=True, save=False)

    report = service.get_last_adjustment_report("ASELS")
    assert report is None
    # No adjustment metadata injected by engine
    assert "adjusted_by_engine" not in mdf.metadata
