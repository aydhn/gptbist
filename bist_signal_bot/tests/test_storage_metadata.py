import pytest
from datetime import datetime
from pathlib import Path
import json

from bist_signal_bot.storage.metadata import (
    StoredMarketDataMetadata,
    MarketDataIndex,
    save_market_data_index,
    load_market_data_index
)
from bist_signal_bot.core.exceptions import StorageError

def test_stored_market_data_metadata_creation():
    now = datetime.utcnow()
    m = StoredMarketDataMetadata(
        symbol="ASELS",
        vendor="yfinance",
        timeframe="1d",
        file_path="/fake/path.csv",
        row_count=100,
        adjusted=True
    )
    assert m.symbol == "ASELS"
    assert m.vendor == "yfinance"
    assert m.timeframe == "1d"
    assert m.adjusted is True
    assert m.schema_version == "1.0"
    assert m.created_at >= now

def test_market_data_index_add_and_get():
    idx = MarketDataIndex()
    m = StoredMarketDataMetadata(
        symbol="ASELS",
        vendor="yfinance",
        timeframe="1d",
        file_path="/fake/path.csv",
        row_count=100,
        adjusted=True
    )

    idx.add_or_update(m)

    res = idx.get("ASELS", "yfinance", "1d")
    assert res is not None
    assert res.symbol == "ASELS"

    assert idx.get("THYAO", "yfinance", "1d") is None

def test_market_data_index_remove():
    idx = MarketDataIndex()
    m = StoredMarketDataMetadata(
        symbol="ASELS",
        vendor="yfinance",
        timeframe="1d",
        file_path="/fake/path.csv",
        row_count=100,
        adjusted=True
    )
    idx.add_or_update(m)
    assert idx.remove("ASELS", "yfinance", "1d") is True
    assert idx.get("ASELS", "yfinance", "1d") is None
    assert idx.remove("ASELS", "yfinance", "1d") is False

def test_save_and_load_market_data_index(tmp_path):
    idx = MarketDataIndex()
    m = StoredMarketDataMetadata(
        symbol="ASELS",
        vendor="yfinance",
        timeframe="1d",
        file_path="/fake/path.csv",
        row_count=100,
        adjusted=True
    )
    idx.add_or_update(m)

    file_path = tmp_path / "index.json"
    save_market_data_index(idx, file_path)

    assert file_path.exists()

    loaded_idx = load_market_data_index(file_path)
    assert len(loaded_idx.items) == 1

    res = loaded_idx.get("ASELS", "yfinance", "1d")
    assert res.symbol == "ASELS"
    assert res.row_count == 100

def test_load_market_data_index_missing_file(tmp_path):
    file_path = tmp_path / "does_not_exist.json"
    idx = load_market_data_index(file_path)
    assert isinstance(idx, MarketDataIndex)
    assert len(idx.items) == 0

def test_load_market_data_index_invalid_json(tmp_path):
    file_path = tmp_path / "invalid.json"
    file_path.write_text("{invalid json}")

    with pytest.raises(StorageError):
        load_market_data_index(file_path)
