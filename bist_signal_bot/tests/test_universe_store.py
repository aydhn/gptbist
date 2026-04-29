import pytest
import json
from pathlib import Path
from bist_signal_bot.data.universe_store import UniverseStore
from bist_signal_bot.core.exceptions import UniverseStoreError
from bist_signal_bot.data.symbol_universe import SymbolUniverse
from bist_signal_bot.data.models import SymbolInfo
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def mock_settings():
    return Settings()

@pytest.fixture
def store(tmp_path, mock_settings):
    mock_settings.UNIVERSE_DIR_NAME = "universe"
    mock_settings.UNIVERSE_FILE_NAME = "bist_universe.json"
    mock_settings.WATCHLISTS_DIR_NAME = "watchlists"
    mock_settings.UNIVERSE_SNAPSHOTS_DIR_NAME = "snapshots"

    return UniverseStore(mock_settings, base_dir=tmp_path)

def test_universe_store_creates_dirs(store):
    assert store.get_universe_dir().exists()
    assert store.get_watchlists_dir().exists()
    assert store.get_snapshots_dir().exists()

def test_initialize_default_universe(store):
    res = store.initialize_default_universe()
    assert res.success
    assert store.exists()

    universe = store.load_universe()
    assert universe.count() > 0

def test_save_and_load_universe(store):
    universe = SymbolUniverse()
    universe.add_symbol(SymbolInfo(symbol="TEST", name="Test"))

    store.save_universe(universe)
    loaded = store.load_universe()

    assert loaded.contains("TEST")

def test_corrupt_json_raises_error(store):
    store.get_universe_dir().mkdir(parents=True, exist_ok=True)
    with open(store.get_universe_file_path(), "w") as f:
        f.write("{invalid_json}")

    with pytest.raises(UniverseStoreError):
        store.load_universe()

def test_watchlist_save_load(store):
    store.save_watchlist("my_list", ["ASELS", "THYAO.IS"])
    loaded = store.load_watchlist("my_list")

    assert len(loaded) == 2
    assert "ASELS" in loaded
    assert "THYAO" in loaded

def test_snapshot_creation(store):
    store.initialize_default_universe()
    path = store.create_snapshot()
    assert path.exists()
