import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from unittest.mock import MagicMock
from bist_signal_bot.cli.commands import (
    cmd_validate_symbol,
    cmd_symbols,
    cmd_mock_data,
    cmd_quality_demo,
    cmd_provider_status,
    cmd_storage_status,
    cmd_calendar_status,
    cmd_telegram_test
)
from bist_signal_bot.app.bootstrap import ApplicationContext
from bist_signal_bot.data.symbol_universe import SymbolUniverse, DEFAULT_SEED_SYMBOLS

@pytest.fixture
def mock_app_context(tmp_path):
    ctx = MagicMock()
    # Replace list_symbols mock to return proper objects
    universe = SymbolUniverse(DEFAULT_SEED_SYMBOLS)
    ctx.symbol_universe = universe

    settings_mock = MagicMock()
    settings_mock.DEFAULT_DATA_PROVIDER = "yfinance"
    settings_mock.DEFAULT_TIMEFRAME = "1d"
    settings_mock.DEFAULT_HISTORY_PERIOD = "2y"
    settings_mock.DATA_DIR = tmp_path
    settings_mock.MARKET_DATA_DIR_NAME = "market_data"
    settings_mock.METADATA_DIR_NAME = "metadata"
    settings_mock.MARKET_DATA_INDEX_FILE = "index.json"
    settings_mock.STORAGE_FORMAT = "csv"
    settings_mock.ENABLE_TELEGRAM = True
    ctx.settings = settings_mock

    ctx.notifier = MagicMock()
    res = MagicMock()
    res.success = True
    res.dry_run = True
    ctx.notifier.send_text.return_value = res
    return ctx

def test_cmd_validate_symbol_valid(mock_app_context):
    args = MagicMock(symbol="ASELS.IS", json=False)
    assert cmd_validate_symbol(args, mock_app_context) == 0

def test_cmd_validate_symbol_invalid(mock_app_context):
    args = MagicMock(symbol="INVALID", json=False)
    assert cmd_validate_symbol(args, mock_app_context) == 1

def test_cmd_symbols(mock_app_context):
    args = MagicMock(json=False, yfinance=False, group=None)
    assert cmd_symbols(args, mock_app_context) == 0

def test_cmd_mock_data(mock_app_context):
    args = MagicMock(symbol="ASELS", rows=10, save=False, json=False)
    assert cmd_mock_data(args, mock_app_context) == 0

def test_cmd_quality_demo(mock_app_context):
    args = MagicMock(symbol="ASELS", rows=20, json=False)
    assert cmd_quality_demo(args, mock_app_context) == 0

def test_cmd_provider_status(mock_app_context):
    args = MagicMock(json=False)
    assert cmd_provider_status(args, mock_app_context) == 0

def test_cmd_storage_status(mock_app_context, monkeypatch):
    import bist_signal_bot.cli.commands as commands
    monkeypatch.setattr(commands, 'get_market_data_dir', lambda x: mock_app_context.settings.DATA_DIR / "md")
    monkeypatch.setattr(commands, 'get_metadata_dir', lambda x: mock_app_context.settings.DATA_DIR / "meta")
    monkeypatch.setattr(commands, 'get_market_data_index_path', lambda x: mock_app_context.settings.DATA_DIR / "idx.json")
    args = MagicMock(json=False)
    assert cmd_storage_status(args, mock_app_context) == 0

def test_cmd_calendar_status(mock_app_context):
    args = MagicMock(json=False, at=None)
    mock_app_context.session_service.get_status.return_value = MagicMock()
    assert cmd_calendar_status(args, mock_app_context) == 0

def test_cmd_telegram_test(mock_app_context):
    args = MagicMock(message="test", json=False)
    assert cmd_telegram_test(args, mock_app_context) == 0
