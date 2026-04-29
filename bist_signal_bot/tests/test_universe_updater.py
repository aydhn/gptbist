import pytest
from pathlib import Path
from bist_signal_bot.data.universe_updater import UniverseUpdater
from bist_signal_bot.data.universe_store import UniverseStore
from bist_signal_bot.data.symbol_universe import SymbolUniverse
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def store(tmp_path):
    settings = Settings()
    settings.UNIVERSE_DIR_NAME = "universe"
    settings.UNIVERSE_FILE_NAME = "bist_universe.json"
    settings.WATCHLISTS_DIR_NAME = "watchlists"
    settings.UNIVERSE_SNAPSHOTS_DIR_NAME = "snapshots"
    return UniverseStore(settings, base_dir=tmp_path)

@pytest.fixture
def updater(store):
    return UniverseUpdater(store, store.settings)

def test_validate_clean_universe(updater, store):
    store.initialize_default_universe()
    universe = store.load_universe()
    report = updater.validate_universe(universe)
    assert report.passed

def test_validate_empty_universe_issue(updater):
    universe = SymbolUniverse()
    report = updater.validate_universe(universe)
    assert not report.passed
    assert len(report.issues) == 1
    assert report.issues[0].issue_type == "EMPTY_UNIVERSE"

def test_add_symbol(updater, store):
    res = updater.add_symbol("YENI")
    assert res.success
    universe = store.load_universe()
    assert universe.contains("YENI")

def test_add_duplicate_symbol(updater, store):
    updater.add_symbol("YENI")
    res = updater.add_symbol("YENI")
    assert not res.success
    assert res.error == "DuplicateSymbol"

def test_deactivate_and_activate_symbol(updater, store):
    updater.add_symbol("TEST1")

    updater.deactivate_symbol("TEST1")
    universe = store.load_universe()
    assert not universe.require("TEST1").is_active

    updater.activate_symbol("TEST1")
    universe = store.load_universe()
    assert universe.require("TEST1").is_active

def test_remove_symbol(updater, store):
    updater.add_symbol("TEST1")
    updater.remove_symbol("TEST1")
    universe = store.load_universe()
    assert not universe.contains("TEST1")

def test_import_from_file_merge(updater, store, tmp_path):
    store.initialize_default_universe()
    import_file = tmp_path / "import.csv"
    with open(import_file, "w") as f:
        f.write("symbol,name,groups,is_active\nTEST1,Test,LIQUID,true\n")

    res = updater.import_from_file(import_file, merge=True)
    assert res.success

    universe = store.load_universe()
    assert universe.contains("TEST1")
    assert universe.count(active_only=False) > 1

def test_import_from_file_deactivate_missing(updater, store, tmp_path):
    store.initialize_default_universe()
    import_file = tmp_path / "import.csv"
    with open(import_file, "w") as f:
        f.write("symbol,name,groups,is_active\nTEST1,Test,LIQUID,true\n")

    res = updater.import_from_file(import_file, merge=True, deactivate_missing=True)
    assert res.success

    universe = store.load_universe()
    assert universe.contains("TEST1")
    assert universe.count(active_only=True) == 1
