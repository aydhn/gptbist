
import pytest

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import InvalidSymbolError
from bist_signal_bot.storage.paths import (
    PROJECT_ROOT,
    get_data_dir,
    get_market_data_dir,
    get_market_data_index_path,
    get_metadata_dir,
    get_ohlcv_dir,
    get_ohlcv_file_path,
)


def test_get_data_dir():
    s = Settings(DATA_DIR="test_data")
    assert get_data_dir(s) == PROJECT_ROOT / "test_data"

def test_get_market_data_dir():
    s = Settings(DATA_DIR="test_data", MARKET_DATA_DIR_NAME="md")
    assert get_market_data_dir(s) == PROJECT_ROOT / "test_data" / "md"

def test_get_ohlcv_dir():
    s = Settings(DATA_DIR="test_data", MARKET_DATA_DIR_NAME="md", OHLCV_DIR_NAME="ohlcv")
    path = get_ohlcv_dir("yfinance", "1d", s)
    assert path == PROJECT_ROOT / "test_data" / "md" / "ohlcv" / "yfinance" / "1d"

def test_get_ohlcv_file_path_valid_symbol():
    s = Settings(DATA_DIR="test_data", MARKET_DATA_DIR_NAME="md", OHLCV_DIR_NAME="ohlcv")
    path = get_ohlcv_file_path("ASELS", "yfinance", "1d", s)
    assert path.name == "ASELS.csv"
    assert path.parent == PROJECT_ROOT / "test_data" / "md" / "ohlcv" / "yfinance" / "1d"

def test_get_ohlcv_file_path_normalizes_symbol():
    s = Settings(DATA_DIR="test_data", MARKET_DATA_DIR_NAME="md", OHLCV_DIR_NAME="ohlcv")
    path = get_ohlcv_file_path("asels.is", "yfinance", "1d", s)
    assert path.name == "ASELS.csv"

def test_get_ohlcv_file_path_invalid_symbol():
    s = Settings(DATA_DIR="test_data")
    with pytest.raises(InvalidSymbolError):
        get_ohlcv_file_path("INVALID!@", "yfinance", "1d", s)

def test_get_metadata_dir():
    s = Settings(DATA_DIR="test_data", MARKET_DATA_DIR_NAME="md", METADATA_DIR_NAME="meta")
    assert get_metadata_dir(s) == PROJECT_ROOT / "test_data" / "md" / "meta"

def test_get_market_data_index_path():
    s = Settings(DATA_DIR="test_data", MARKET_DATA_DIR_NAME="md", METADATA_DIR_NAME="meta", MARKET_DATA_INDEX_FILE="index.json")
    assert get_market_data_index_path(s) == PROJECT_ROOT / "test_data" / "md" / "meta" / "index.json"
