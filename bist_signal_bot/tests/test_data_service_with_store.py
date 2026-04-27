import pytest
import pandas as pd
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.mock_provider import MockMarketDataProvider
from bist_signal_bot.data.symbol_universe import SymbolUniverse
from bist_signal_bot.storage.local_store import LocalMarketDataStore
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.data.models import Timeframe, SymbolInfo

@pytest.fixture
def test_settings(tmp_path):
    return Settings(
        DATA_DIR=str(tmp_path / "data"),
        MARKET_DATA_DIR_NAME="market_data",
        OHLCV_DIR_NAME="ohlcv",
        METADATA_DIR_NAME="metadata",
        MARKET_DATA_INDEX_FILE="index.json",
        STORAGE_FORMAT="csv"
    )

@pytest.fixture
def store(test_settings):
    return LocalMarketDataStore(settings=test_settings)

@pytest.fixture
def provider():
    return MockMarketDataProvider()

@pytest.fixture
def universe():
    u = SymbolUniverse([])
    u.add_symbol(SymbolInfo(symbol="ASELS"))
    u.add_symbol(SymbolInfo(symbol="THYAO"))
    return u

def test_data_service_fetches_and_saves(provider, universe, store):
    service = MarketDataService(provider=provider, universe=universe, store=store, prefer_local=True)

    assert store.exists("ASELS", provider.vendor, Timeframe.DAILY) is False

    mdf = service.get_ohlcv("ASELS", Timeframe.DAILY)
    assert not mdf.is_empty()

    # Should now be in store
    assert store.exists("ASELS", provider.vendor, Timeframe.DAILY) is True

def test_data_service_reads_from_local(provider, universe, store):
    service = MarketDataService(provider=provider, universe=universe, store=store, prefer_local=True)

    # Fetch once to populate local store
    service.get_ohlcv("ASELS", Timeframe.DAILY)

    # Check if exists
    assert store.exists("ASELS", provider.vendor, Timeframe.DAILY) is True

    # Now monkeypatch provider to raise an exception.
    # If it reads from local, it won't hit the exception.
    def mock_fetch_one(*args, **kwargs):
        raise Exception("Should not be called")

    provider.fetch_one = mock_fetch_one

    mdf = service.get_ohlcv("ASELS", Timeframe.DAILY)
    assert mdf.symbol == "ASELS"

def test_data_service_refresh_skips_local(provider, universe, store):
    service = MarketDataService(provider=provider, universe=universe, store=store, prefer_local=True)

    # Fetch once to populate local store
    service.get_ohlcv("ASELS", Timeframe.DAILY)

    # Now monkeypatch provider to track calls
    call_count = 0
    original_fetch = provider.fetch_one
    def mock_fetch_one(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return original_fetch(*args, **kwargs)

    provider.fetch_one = mock_fetch_one

    # refresh=True should hit provider
    service.get_ohlcv("ASELS", Timeframe.DAILY, refresh=True)
    assert call_count == 1

def test_data_service_save_false_skips_writing(provider, universe, store):
    service = MarketDataService(provider=provider, universe=universe, store=store, prefer_local=True)

    service.get_ohlcv("ASELS", Timeframe.DAILY, save=False)

    assert store.exists("ASELS", provider.vendor, Timeframe.DAILY) is False
