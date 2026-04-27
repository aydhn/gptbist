from collections.abc import Iterable

from bist_signal_bot.core.exceptions import DuplicateSymbolError, SymbolUniverseError
from bist_signal_bot.data.models import SymbolGroup, SymbolInfo
from bist_signal_bot.data.symbol_utils import normalize_symbol, to_yfinance_symbol

# Seed list - This is a starter watchlist, not an official index composition claim.
DEFAULT_SEED_SYMBOLS_STR = [
    "THYAO", "ASELS", "KCHOL", "SAHOL", "TUPRS", "SISE", "EREGL",
    "GARAN", "AKBNK", "ISCTR", "YKBNK", "BIMAS", "FROTO", "TOASO",
    "TCELL", "ENKAI", "PETKM", "KOZAL", "KRDMD", "ARCLK"
]

DEFAULT_SEED_SYMBOLS = [
    SymbolInfo(symbol=sym, groups={SymbolGroup.LIQUID, SymbolGroup.WATCHLIST})
    for sym in DEFAULT_SEED_SYMBOLS_STR
]

class SymbolUniverse:
    def __init__(self, symbols: Iterable[SymbolInfo] | None = None):
        self._symbols: dict[str, SymbolInfo] = {}
        if symbols:
            for symbol_info in symbols:
                self.add_symbol(symbol_info)

    def add_symbol(self, symbol_info: SymbolInfo) -> None:
        """Adds a symbol to the universe."""
        if symbol_info.symbol in self._symbols:
            raise DuplicateSymbolError(f"Symbol '{symbol_info.symbol}' already exists in universe.")
        self._symbols[symbol_info.symbol] = symbol_info

    def remove_symbol(self, symbol: str) -> None:
        """Removes a symbol from the universe."""
        normalized = normalize_symbol(symbol)
        if normalized in self._symbols:
            del self._symbols[normalized]

    def deactivate_symbol(self, symbol: str) -> None:
        """Deactivates a symbol in the universe."""
        normalized = normalize_symbol(symbol)
        if normalized in self._symbols:
            self._symbols[normalized].is_active = False

    def activate_symbol(self, symbol: str) -> None:
        """Activates a symbol in the universe."""
        normalized = normalize_symbol(symbol)
        if normalized in self._symbols:
            self._symbols[normalized].is_active = True

    def get(self, symbol: str) -> SymbolInfo | None:
        """Gets a SymbolInfo by symbol."""
        normalized = normalize_symbol(symbol)
        return self._symbols.get(normalized)

    def require(self, symbol: str) -> SymbolInfo:
        """Gets a SymbolInfo by symbol, raises error if not found."""
        normalized = normalize_symbol(symbol)
        info = self._symbols.get(normalized)
        if info is None:
            raise SymbolUniverseError(f"Symbol '{normalized}' not found in universe.")
        return info

    def contains(self, symbol: str) -> bool:
        """Checks if a symbol exists in the universe."""
        normalized = normalize_symbol(symbol)
        return normalized in self._symbols

    def list_symbols(self, active_only: bool = True) -> list[str]:
        """Lists all symbols in internal format."""
        if active_only:
            return [sym for sym, info in self._symbols.items() if info.is_active]
        return list(self._symbols.keys())

    def list_yfinance_symbols(self, active_only: bool = True) -> list[str]:
        """Lists all symbols in yfinance format."""
        return [to_yfinance_symbol(sym) for sym in self.list_symbols(active_only=active_only)]

    def filter_by_group(self, group: SymbolGroup, active_only: bool = True) -> list[SymbolInfo]:
        """Returns SymbolInfo objects that belong to a specific group."""
        result = []
        for info in self._symbols.values():
            if group in info.groups:
                if not active_only or info.is_active:
                    result.append(info)
        return result

    def count(self, active_only: bool = True) -> int:
        """Returns the count of symbols."""
        if active_only:
            return sum(1 for info in self._symbols.values() if info.is_active)
        return len(self._symbols)

    def validate_unique_symbols(self) -> None:
        """Utility method to ensure no duplicates exist (already enforced by dict/add_symbol)."""
        pass
