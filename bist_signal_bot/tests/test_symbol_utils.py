import pytest
from bist_signal_bot.data.symbol_utils import (
    normalize_symbol,
    validate_internal_symbol,
    ensure_valid_internal_symbol,
    to_yfinance_symbol,
    from_yfinance_symbol,
    symbol_matches
)
from bist_signal_bot.core.exceptions import InvalidSymbolError

def test_normalize_symbol():
    assert normalize_symbol("asels") == "ASELS"
    assert normalize_symbol("ASELS.IS") == "ASELS"
    assert normalize_symbol(" thyao.is ") == "THYAO"
    assert normalize_symbol("GARAN") == "GARAN"
    assert normalize_symbol("") == ""

def test_validate_internal_symbol():
    assert validate_internal_symbol("ASELS") is True
    assert validate_internal_symbol("ASELS.IS") is False
    assert validate_internal_symbol(" ASELS ") is False
    assert validate_internal_symbol("ASELS123") is True
    assert validate_internal_symbol("") is False

def test_ensure_valid_internal_symbol():
    assert ensure_valid_internal_symbol("asels") == "ASELS"
    assert ensure_valid_internal_symbol("ASELS.IS") == "ASELS"

    with pytest.raises(InvalidSymbolError):
        ensure_valid_internal_symbol("AS ELS")

    with pytest.raises(InvalidSymbolError):
        ensure_valid_internal_symbol("ASELŞ") # Turkish char

def test_to_yfinance_symbol():
    assert to_yfinance_symbol("ASELS") == "ASELS.IS"
    assert to_yfinance_symbol("asels") == "ASELS.IS"

def test_from_yfinance_symbol():
    assert from_yfinance_symbol("ASELS.IS") == "ASELS"
    assert from_yfinance_symbol(" thyao.is ") == "THYAO"

def test_symbol_matches():
    assert symbol_matches("ASELS", "asels.is") is True
    assert symbol_matches("THYAO", "THYAO") is True
    assert symbol_matches("GARAN.IS", "garan") is True
    assert symbol_matches("ASELS", "THYAO") is False
