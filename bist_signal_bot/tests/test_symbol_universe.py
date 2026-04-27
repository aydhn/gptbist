import pytest

from bist_signal_bot.core.exceptions import DuplicateSymbolError, SymbolUniverseError
from bist_signal_bot.data.models import SymbolGroup, SymbolInfo
from bist_signal_bot.data.symbol_universe import SymbolUniverse


@pytest.fixture
def empty_universe():
    return SymbolUniverse()

@pytest.fixture
def populated_universe():
    symbols = [
        SymbolInfo(symbol="ASELS", groups={SymbolGroup.BIST30}),
        SymbolInfo(symbol="THYAO", groups={SymbolGroup.BIST30}),
        SymbolInfo(symbol="GARAN", is_active=False)
    ]
    return SymbolUniverse(symbols)

def test_add_symbol(empty_universe):
    info = SymbolInfo(symbol="KCHOL")
    empty_universe.add_symbol(info)
    assert empty_universe.contains("KCHOL")
    assert empty_universe.count() == 1

def test_add_duplicate_symbol(populated_universe):
    info = SymbolInfo(symbol="asels.is") # Should normalize to ASELS
    with pytest.raises(DuplicateSymbolError):
        populated_universe.add_symbol(info)

def test_get_symbol(populated_universe):
    info = populated_universe.get("asels.is")
    assert info is not None
    assert info.symbol == "ASELS"

    assert populated_universe.get("UNKNOWN") is None

def test_require_symbol(populated_universe):
    info = populated_universe.require("ASELS")
    assert info.symbol == "ASELS"

    with pytest.raises(SymbolUniverseError):
        populated_universe.require("UNKNOWN")

def test_active_count(populated_universe):
    assert populated_universe.count(active_only=True) == 2
    assert populated_universe.count(active_only=False) == 3

def test_list_yfinance_symbols(populated_universe):
    yf_symbols = populated_universe.list_yfinance_symbols(active_only=True)
    assert len(yf_symbols) == 2
    assert "ASELS.IS" in yf_symbols
    assert "THYAO.IS" in yf_symbols
    assert "GARAN.IS" not in yf_symbols

def test_filter_by_group(populated_universe):
    bist30 = populated_universe.filter_by_group(SymbolGroup.BIST30)
    assert len(bist30) == 2

    # Add a disabled BIST30 stock
    populated_universe.add_symbol(SymbolInfo(symbol="AKBNK", groups={SymbolGroup.BIST30}, is_active=False))

    bist30_active = populated_universe.filter_by_group(SymbolGroup.BIST30, active_only=True)
    assert len(bist30_active) == 2

    bist30_all = populated_universe.filter_by_group(SymbolGroup.BIST30, active_only=False)
    assert len(bist30_all) == 3

def test_deactivate_activate(populated_universe):
    populated_universe.deactivate_symbol("ASELS")
    assert populated_universe.get("ASELS").is_active is False
    assert populated_universe.count(active_only=True) == 1

    populated_universe.activate_symbol("ASELS")
    assert populated_universe.get("ASELS").is_active is True
    assert populated_universe.count(active_only=True) == 2
