import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from unittest.mock import MagicMock
from bist_signal_bot.cli.commands import cmd_clean_data

@pytest.fixture
def mock_app_context(tmp_path):
    ctx = MagicMock()
    settings_mock = MagicMock()
    settings_mock.DEFAULT_DATA_PROVIDER = "yfinance"
    settings_mock.DEFAULT_TIMEFRAME = "1d"
    settings_mock.DATA_DIR = tmp_path
    settings_mock.MARKET_DATA_DIR_NAME = "market_data"
    settings_mock.OHLCV_DIR_NAME = "ohlcv"
    settings_mock.METADATA_DIR_NAME = "metadata"
    settings_mock.MARKET_DATA_INDEX_FILE = "index.json"
    settings_mock.STORAGE_FORMAT = "csv"
    settings_mock.CLEANING_STRICT = False
    settings_mock.CLEANING_MISSING_VALUE_POLICY = "FORWARD_FILL"
    settings_mock.CLEANING_INVALID_OHLC_POLICY = "DROP_ROW"
    settings_mock.CLEANING_OUTLIER_POLICY = "FLAG_ONLY"
    settings_mock.CLEANING_DUPLICATE_TIMESTAMP_POLICY = "KEEP_LAST"
    settings_mock.CLEANING_MAX_DAILY_RETURN_ABS = 0.35
    settings_mock.CLEANING_MAX_VOLUME_ZSCORE = 8.0
    settings_mock.CLEANING_MIN_ROWS_AFTER_CLEANING = 100


    ctx.settings = settings_mock
    return ctx

def test_cmd_clean_data_mock(mock_app_context):
    args = MagicMock(
        symbol="ASELS",
        source="mock",
        timeframe="1d",
        save=False,
        policy_missing=None,
        policy_invalid_ohlc=None,
        policy_outlier=None,
        policy_duplicate=None,
        strict=False,
        json=False
    )

    # Execution
    ret = cmd_clean_data(args, mock_app_context)

    # Should be 0 (success)
    assert ret == 0

def test_cmd_clean_data_json(mock_app_context):
    args = MagicMock(
        symbol="ASELS",
        source="mock",
        timeframe="1d",
        save=False,
        policy_missing=None,
        policy_invalid_ohlc=None,
        policy_outlier=None,
        policy_duplicate=None,
        strict=False,
        json=True
    )

    ret = cmd_clean_data(args, mock_app_context)
    assert ret == 0
