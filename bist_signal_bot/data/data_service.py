import logging
from typing import Any

from bist_signal_bot.core.exceptions import (
    DataQualityError,
    InvalidSymbolError,
    SymbolUniverseError,
)
from bist_signal_bot.data.base_provider import BaseMarketDataProvider
from bist_signal_bot.data.models import DataFetchRequest, MarketDataFrame, Timeframe
from bist_signal_bot.data.quality import DataQualityChecker, DataQualityReport
from bist_signal_bot.data.symbol_universe import SymbolUniverse
from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
from bist_signal_bot.storage.local_store import LocalMarketDataStore

logger = logging.getLogger(__name__)

class MarketDataService:
    """
    Service layer to handle data fetching from a provider.
    Integrates with SymbolUniverse, local storage, and validates incoming requests.
    """

    def __init__(
        self,
        provider: BaseMarketDataProvider,
        universe: SymbolUniverse | None = None,
        store: LocalMarketDataStore | None = None,
        prefer_local: bool = True,
        quality_checker: DataQualityChecker | None = None,
        validate_quality: bool = True,
        fail_on_quality_error: bool = False
    ):
        self.provider = provider
        self.universe = universe
        self.store = store
        self.prefer_local = prefer_local
        self.quality_checker = quality_checker or DataQualityChecker()
        self.validate_quality = validate_quality
        self.fail_on_quality_error = fail_on_quality_error
        self.last_quality_reports: dict[str, DataQualityReport] = {}

    def _validate_symbol(self, symbol: str) -> None:
        try:
            ensure_valid_internal_symbol(symbol)
        except Exception as e:
            raise InvalidSymbolError(f"Symbol '{symbol}' is not a valid internal format: {e}")

        if self.universe:
            if not self.universe.contains(symbol):
                raise SymbolUniverseError(f"Symbol '{symbol}' not found in the configured SymbolUniverse.")

    def _apply_quality_check(self, mdf: MarketDataFrame, symbol: str) -> MarketDataFrame:
        if not self.validate_quality or not self.quality_checker:
            return mdf

        report = self.quality_checker.check(mdf)
        self.last_quality_reports[symbol] = report
        mdf.quality_report = report

        if self.fail_on_quality_error and (report.has_critical() or report.has_errors()):
            raise DataQualityError(f"Data quality checks failed for {symbol}. Critical: {report.has_critical()}, Errors: {report.error_count()}")

        return mdf

    def get_last_quality_report(self, symbol: str) -> DataQualityReport | None:
        return self.last_quality_reports.get(symbol)

    def get_ohlcv(self, symbol: str, timeframe: Timeframe = Timeframe.DAILY, period: str = "2y", refresh: bool = False, save: bool = True) -> MarketDataFrame:
        """Fetch historical data for a single symbol, utilizing local storage if available and preferred."""
        self._validate_symbol(symbol)

        # Check local storage if preferred and refresh not requested
        if self.store and self.prefer_local and not refresh:
            if self.store.exists(symbol, self.provider.vendor, timeframe):
                logger.debug(f"Reading {symbol} from local store.")
                try:
                    mdf = self.store.read_ohlcv(symbol, self.provider.vendor, timeframe)
                    # We might want to check if the date range in local store satisfies 'period',
                    # but for this phase we assume local data is sufficient if it exists.
                    return self._apply_quality_check(mdf, symbol)
                except Exception as e:
                    logger.warning(f"Failed to read local data for {symbol}, falling back to provider: {e}")

        logger.debug(f"Fetching {symbol} from provider.")
        mdf = self.provider.fetch_one(
            symbol=symbol,
            timeframe=timeframe,
            period=period
        )

        mdf.validate_schema()

        mdf = self._apply_quality_check(mdf, symbol)

        if self.store and save:
            logger.debug(f"Saving {symbol} to local store.")
            self.store.write_ohlcv(mdf)

        return mdf

    def get_many_ohlcv(self, symbols: list[str], timeframe: Timeframe = Timeframe.DAILY, period: str = "2y", refresh: bool = False, save: bool = True) -> dict[str, MarketDataFrame]:
        """Fetch historical data for multiple symbols, utilizing local storage."""
        results = {}
        symbols_to_fetch = []

        for sym in symbols:
            self._validate_symbol(sym)

            if self.store and self.prefer_local and not refresh:
                if self.store.exists(sym, self.provider.vendor, timeframe):
                    try:
                        mdf = self.store.read_ohlcv(sym, self.provider.vendor, timeframe)
                        results[sym] = self._apply_quality_check(mdf, sym)
                        continue
                    except Exception as e:
                        logger.warning(f"Failed to read local data for {sym}, will fetch: {e}")

            symbols_to_fetch.append(sym)

        if symbols_to_fetch:
            req = DataFetchRequest(
                symbols=symbols_to_fetch,
                timeframe=timeframe,
                period=period
            )

            provider_results = self.provider.fetch_ohlcv(req)

            for sym, mdf in provider_results.items():
                mdf.validate_schema()
                mdf = self._apply_quality_check(mdf, sym)
                results[sym] = mdf

                if self.store and save:
                    self.store.write_ohlcv(mdf)

        return results

    def provider_status(self) -> dict[str, Any]:
        """Return the current status of the configured data provider and storage."""
        data_dir = None
        if self.store and self.store.settings:
            # Reconstruct the expected data dir path string roughly
            data_dir = str(self.store.settings.DATA_DIR)

        return {
            "name": self.provider.name,
            "vendor": self.provider.vendor.value,
            "is_available": self.provider.is_available(),
            "supports_intraday": self.provider.supports_intraday,
            "supports_adjusted": self.provider.supports_adjusted,
            "has_store": self.store is not None,
            "prefer_local": self.prefer_local,
            "data_dir": data_dir
        }
