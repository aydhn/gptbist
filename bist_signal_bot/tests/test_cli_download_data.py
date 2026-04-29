import pytest
from unittest.mock import MagicMock
from bist_signal_bot.data.mock_provider import MockMarketDataProvider
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.cli.commands import cmd_download_data
from bist_signal_bot.data.symbol_universe import SymbolUniverse, DEFAULT_SEED_SYMBOLS

@pytest.fixture
def mock_app_context(tmp_path):
    ctx = MagicMock()
    universe = SymbolUniverse(DEFAULT_SEED_SYMBOLS)
    ctx.symbol_universe = universe

    settings_mock = MagicMock()
    settings_mock.DEFAULT_DATA_PROVIDER = "mock"
    settings_mock.DEFAULT_TIMEFRAME = "1d"
    settings_mock.DEFAULT_HISTORY_PERIOD = "2y"
    settings_mock.DATA_DIR = tmp_path
    settings_mock.MARKET_DATA_DIR_NAME = "market_data"
    settings_mock.METADATA_DIR_NAME = "metadata"
    settings_mock.MARKET_DATA_INDEX_FILE = "index.json"
    settings_mock.STORAGE_FORMAT = "csv"
    settings_mock.DOWNLOAD_DEFAULT_PERIOD = "2y"
    settings_mock.DOWNLOAD_CONTINUE_ON_ERROR = True
    settings_mock.DOWNLOAD_SEND_TELEGRAM_SUMMARY = False

    settings_mock.ENABLE_DATA_NORMALIZATION = True
    settings_mock.NORMALIZATION_TARGET_TIMEZONE = "Europe/Istanbul"
    settings_mock.NORMALIZATION_DROP_UNKNOWN_COLUMNS = False
    settings_mock.NORMALIZATION_DEDUPLICATE_INDEX = True
    settings_mock.NORMALIZATION_SORT_INDEX = True
    settings_mock.NORMALIZATION_STRICT = False
    settings_mock.NORMALIZATION_FAIL_ON_ERROR = True

    ctx.settings = settings_mock

    ctx.notifier = MagicMock()
    ctx.audit_logger = MagicMock()

    from bist_signal_bot.storage.local_store import LocalMarketDataStore
    ctx.local_store = LocalMarketDataStore(settings_mock)

    # We must properly initialize the data_service to use Mock
    ctx.data_service = MarketDataService(provider=MockMarketDataProvider(), store=ctx.local_store)
    return ctx


def test_cli_download_single(mock_app_context):
    args = MagicMock(
        symbols=["ASELS"],
        all=False, group=None, timeframe="1d", period="2y",
        refresh=False, save=False, continue_on_error=True, fail_fast=False,
        telegram_summary=False, json=False
    )
    assert cmd_download_data(args, mock_app_context) == 0

def test_cli_download_batch(mock_app_context):
    args = MagicMock(
        symbols=["ASELS", "THYAO"],
        all=False, group=None, timeframe="1d", period="2y",
        refresh=False, save=False, continue_on_error=True, fail_fast=False,
        telegram_summary=False, json=False
    )
    assert cmd_download_data(args, mock_app_context) == 0
