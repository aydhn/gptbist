import pytest

from bist_signal_bot.core.exceptions import InvalidSymbolError
from bist_signal_bot.data.models import AssetType, Market, SymbolGroup, SymbolInfo


def test_symbol_info_normalization():
    info = SymbolInfo(symbol="asels.is")
    assert info.symbol == "ASELS"
    assert info.market == Market.BIST
    assert info.asset_type == AssetType.EQUITY
    assert info.currency == "TRY"
    assert info.is_active is True
    assert info.groups == set()

def test_symbol_info_invalid_symbol():
    with pytest.raises(InvalidSymbolError):
        SymbolInfo(symbol="AS ELS")

    with pytest.raises(ValueError):
        SymbolInfo(symbol="")

def test_symbol_info_groups():
    info = SymbolInfo(symbol="THYAO", groups={SymbolGroup.BIST30, SymbolGroup.LIQUID})
    assert SymbolGroup.BIST30 in info.groups
    assert SymbolGroup.LIQUID in info.groups
