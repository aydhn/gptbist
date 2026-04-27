import re
from bist_signal_bot.core.constants import YFINANCE_BIST_SUFFIX, INTERNAL_SYMBOL_PATTERN
from bist_signal_bot.core.exceptions import InvalidSymbolError

def normalize_symbol(symbol: str) -> str:
    """
    Cleans the symbol, converts to uppercase, strips whitespace,
    and removes the .IS suffix if present to return internal format.
    """
    if not symbol:
        return ""
    cleaned = symbol.strip().upper()
    if cleaned.endswith(YFINANCE_BIST_SUFFIX):
        cleaned = cleaned[:-len(YFINANCE_BIST_SUFFIX)]
    return cleaned

def validate_internal_symbol(symbol: str) -> bool:
    """
    Checks if the symbol matches internal format rules (A-Z, 0-9 only).
    """
    if not symbol:
        return False
    return bool(re.match(INTERNAL_SYMBOL_PATTERN, symbol))

def ensure_valid_internal_symbol(symbol: str) -> str:
    """
    Normalizes the symbol and raises InvalidSymbolError if it's invalid.
    """
    normalized = normalize_symbol(symbol)
    if not validate_internal_symbol(normalized):
        raise InvalidSymbolError(f"Symbol '{symbol}' (normalized: '{normalized}') is not a valid internal symbol.")
    return normalized

def to_yfinance_symbol(symbol: str) -> str:
    """
    Converts internal symbol to yfinance format (e.g., ASELS -> ASELS.IS).
    """
    # Assuming symbol is already internal format or can be normalized
    normalized = normalize_symbol(symbol)
    if not normalized:
        return ""
    return f"{normalized}{YFINANCE_BIST_SUFFIX}"

def from_yfinance_symbol(symbol: str) -> str:
    """
    Converts yfinance format back to internal format (e.g., ASELS.IS -> ASELS).
    """
    return normalize_symbol(symbol)

def symbol_matches(symbol_a: str, symbol_b: str) -> bool:
    """
    Checks if two symbols are the same, handling case and .IS suffix differences.
    """
    return normalize_symbol(symbol_a) == normalize_symbol(symbol_b)
