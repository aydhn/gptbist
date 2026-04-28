import pytest
from datetime import datetime, UTC
import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.downloader import MarketDataDownloader
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.data.mock_provider import MockMarketDataProvider
from bist_signal_bot.storage.local_store import LocalMarketDataStore
from bist_signal_bot.data.symbol_universe import SymbolUniverse, DEFAULT_SEED_SYMBOLS
from bist_signal_bot.data.models import DownloadStatus, Timeframe

@pytest.fixture
def mock_downloader(tmp_path):
    settings = Settings(DATA_DIR=str(tmp_path), RUN_MODE="research")
    universe = SymbolUniverse(DEFAULT_SEED_SYMBOLS)
    store = LocalMarketDataStore(settings)
    provider = MockMarketDataProvider(rows=50)
    service = MarketDataService(provider=provider, universe=universe, store=store, prefer_local=True)
    return MarketDataDownloader(
        data_service=service,
        universe=universe,
        settings=settings
    )

def test_download_single_symbol_success(mock_downloader):
    res = mock_downloader.download_symbol("ASELS", save=False)
    assert res.status == DownloadStatus.SUCCESS
    assert res.symbol == "ASELS"
    assert res.row_count > 0
    assert not res.saved
    assert not res.from_cache

def test_download_single_symbol_with_save(mock_downloader):
    res = mock_downloader.download_symbol("THYAO", save=True)
    assert res.status == DownloadStatus.SUCCESS
    assert res.saved
    assert res.file_path is not None
    assert not res.from_cache

def test_download_single_symbol_from_cache(mock_downloader):
    # First download and save
    mock_downloader.download_symbol("GARAN", save=True)

    # Second download should hit cache
    res = mock_downloader.download_symbol("GARAN", save=False, refresh=False)
    assert res.status == DownloadStatus.SUCCESS
    assert res.from_cache

def test_download_single_symbol_refresh(mock_downloader):
    # First download and save
    mock_downloader.download_symbol("AKBNK", save=True)

    # Second download with refresh
    res = mock_downloader.download_symbol("AKBNK", save=False, refresh=True)
    assert res.status == DownloadStatus.SUCCESS
    assert not res.from_cache

def test_download_invalid_symbol(mock_downloader):
    res = mock_downloader.download_symbol("INVALID123", save=False)
    assert res.status == DownloadStatus.FAILED
    assert "not found in Universe" in res.error
