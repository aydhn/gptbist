import pytest
import pandas as pd
from datetime import datetime
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.models import MarketDataFrame, Timeframe, DataVendor
from bist_signal_bot.storage.local_store import LocalMarketDataStore
from bist_signal_bot.core.exceptions import MarketDataStoreError

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
def sample_mdf():
    dates = pd.date_range("2023-01-01", periods=5, tz="Europe/Istanbul")
    df = pd.DataFrame({
        "open": [10, 11, 12, 11, 10],
        "high": [12, 13, 14, 13, 12],
        "low": [9, 10, 11, 10, 9],
        "close": [11, 12, 11, 10, 11],
        "volume": [100, 150, 200, 150, 100]
    }, index=dates)
    df.index.name = "timestamp"

    return MarketDataFrame(
        symbol="ASELS",
        timeframe=Timeframe.DAILY,
        source=DataVendor.YFINANCE,
        data=df,
        fetched_at=datetime.utcnow()
    )

def test_local_store_init(test_settings):
    store = LocalMarketDataStore(settings=test_settings)
    assert store.format == "csv"
    assert store.index is not None

def test_local_store_write_and_read(test_settings, sample_mdf):
    store = LocalMarketDataStore(settings=test_settings)

    # Write
    metadata = store.write_ohlcv(sample_mdf)
    assert metadata.symbol == "ASELS"
    assert metadata.row_count == 5
    assert Path(metadata.file_path).exists()

    # Read
    mdf = store.read_ohlcv("ASELS", DataVendor.YFINANCE, Timeframe.DAILY)
    assert mdf.symbol == "ASELS"
    assert mdf.row_count() == 5
    assert mdf.data.index.name == "timestamp"
    assert "open" in mdf.data.columns

def test_local_store_exists(test_settings, sample_mdf):
    store = LocalMarketDataStore(settings=test_settings)
    assert store.exists("ASELS", "yfinance", "1d") is False

    store.write_ohlcv(sample_mdf)
    assert store.exists("ASELS", "yfinance", "1d") is True

def test_local_store_delete(test_settings, sample_mdf):
    store = LocalMarketDataStore(settings=test_settings)
    store.write_ohlcv(sample_mdf)

    assert store.exists("ASELS", "yfinance", "1d") is True

    deleted = store.delete_ohlcv("ASELS", "yfinance", "1d")
    assert deleted is True
    assert store.exists("ASELS", "yfinance", "1d") is False

    # Check if file is actually deleted
    assert not store.list_available_symbols()

def test_local_store_read_missing_raises(test_settings):
    store = LocalMarketDataStore(settings=test_settings)
    with pytest.raises(MarketDataStoreError):
        store.read_ohlcv("MISSING", "yfinance", "1d")

def test_local_store_list_available(test_settings, sample_mdf):
    store = LocalMarketDataStore(settings=test_settings)
    store.write_ohlcv(sample_mdf)

    symbols = store.list_available_symbols()
    assert symbols == ["ASELS"]

    symbols_filtered = store.list_available_symbols(vendor="mock")
    assert symbols_filtered == []
