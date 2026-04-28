import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.downloader import MarketDataDownloader
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.data.mock_provider import MockMarketDataProvider
from bist_signal_bot.storage.local_store import LocalMarketDataStore
from bist_signal_bot.data.symbol_universe import SymbolUniverse, DEFAULT_SEED_SYMBOLS, SymbolGroup
from bist_signal_bot.data.models import DownloadStatus

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

def test_download_symbols_batch(mock_downloader):
    res = mock_downloader.download_symbols(["ASELS", "THYAO"], save=False)
    assert res.requested_count == 2
    assert res.success_count == 2
    assert res.failed_count == 0
    assert len(res.success_symbols()) == 2
    assert len(res.failed_symbols()) == 0

def test_download_symbols_batch_with_invalid(mock_downloader):
    res = mock_downloader.download_symbols(["ASELS", "INVALID"], save=False, continue_on_error=True)
    assert res.requested_count == 2
    assert res.success_count == 1
    assert res.failed_count == 1
    assert "ASELS" in res.success_symbols()
    assert "INVALID" in res.failed_symbols()

def test_download_symbols_batch_fail_fast(mock_downloader):
    res = mock_downloader.download_symbols(["INVALID", "ASELS"], save=False, continue_on_error=False)
    assert res.requested_count == 2
    assert res.failed_count == 1
    assert res.success_count == 0 # It stopped on the first one
    assert "INVALID" in res.failed_symbols()

def test_download_universe(mock_downloader):
    # Only download a few for speed or just check requested count
    res = mock_downloader.download_universe(group=SymbolGroup.LIQUID, save=False)
    assert res.requested_count > 0
    assert res.success_count == res.requested_count

def test_batch_summary(mock_downloader):
    res = mock_downloader.download_symbols(["ASELS"], save=False)
    summary = res.summary()
    assert summary["requested_count"] == 1
    assert summary["success_count"] == 1
    assert summary["failed_count"] == 0
    assert "elapsed_seconds" in summary
    assert summary["save"] is False
