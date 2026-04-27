from typing import Any

from bist_signal_bot.data.base_provider import BaseMarketDataProvider
from bist_signal_bot.data.symbol_universe import SymbolUniverse
from bist_signal_bot.data.models import MarketDataFrame, Timeframe, DataFetchRequest
from bist_signal_bot.core.exceptions import SymbolUniverseError, InvalidSymbolError
from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol

class MarketDataService:
    """
    Service layer to handle data fetching from a provider.
    Integrates with SymbolUniverse and validates incoming requests.
    """

    def __init__(self, provider: BaseMarketDataProvider, universe: SymbolUniverse | None = None):
        self.provider = provider
        self.universe = universe

    def _validate_symbol(self, symbol: str) -> None:
        try:
            ensure_valid_internal_symbol(symbol)
        except Exception as e:
            raise InvalidSymbolError(f"Symbol '{symbol}' is not a valid internal format: {e}")

        if self.universe:
            if not self.universe.contains(symbol):
                raise SymbolUniverseError(f"Symbol '{symbol}' not found in the configured SymbolUniverse.")

    def get_ohlcv(self, symbol: str, timeframe: Timeframe = Timeframe.DAILY, period: str = "2y") -> MarketDataFrame:
        """Fetch historical data for a single symbol."""
        self._validate_symbol(symbol)

        mdf = self.provider.fetch_one(
            symbol=symbol,
            timeframe=timeframe,
            period=period
        )

        mdf.validate_schema()
        return mdf

    def get_many_ohlcv(self, symbols: list[str], timeframe: Timeframe = Timeframe.DAILY, period: str = "2y") -> dict[str, MarketDataFrame]:
        """Fetch historical data for multiple symbols."""
        for sym in symbols:
            self._validate_symbol(sym)

        req = DataFetchRequest(
            symbols=symbols,
            timeframe=timeframe,
            period=period
        )

        results = self.provider.fetch_ohlcv(req)

        for sym, mdf in results.items():
            mdf.validate_schema()

        return results

    def provider_status(self) -> dict[str, Any]:
        """Return the current status of the configured data provider."""
        return {
            "name": self.provider.name,
            "vendor": self.provider.vendor.value,
            "is_available": self.provider.is_available(),
            "supports_intraday": self.provider.supports_intraday,
            "supports_adjusted": self.provider.supports_adjusted
        }
