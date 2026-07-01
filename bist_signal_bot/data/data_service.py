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

from bist_signal_bot.data.cleaning import MarketDataCleaner

from bist_signal_bot.data.adjustments import PriceAdjustmentEngine
from bist_signal_bot.data.models import AdjustmentReport


logger = logging.getLogger("bist_signal_bot.data_service")

from dataclasses import dataclass

@dataclass
class MarketDataServiceConfig:
    prefer_local: bool = True
    validate_quality: bool = True
    fail_on_quality_error: bool = False
    clean_data: bool = True
    fail_on_cleaning_error: bool = False
    apply_price_adjustments: bool = False
    fail_on_adjustment_error: bool = True

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
        quality_checker: DataQualityChecker | None = None,
        cleaner: MarketDataCleaner | None = None,
        adjustment_engine: PriceAdjustmentEngine | None = None,
        config: MarketDataServiceConfig | None = None
    ):
        config = config or MarketDataServiceConfig()

        self.provider = provider
        self.universe = universe
        self.store = store
        self.prefer_local = config.prefer_local
        self.quality_checker = quality_checker or DataQualityChecker()
        self.validate_quality = config.validate_quality
        self.fail_on_quality_error = config.fail_on_quality_error
        self.last_quality_reports: dict[str, DataQualityReport] = {}


        self.cleaner = cleaner or MarketDataCleaner()
        self.clean_data = config.clean_data
        self.fail_on_cleaning_error = config.fail_on_cleaning_error
        self.last_cleaning_reports = {}

        self.adjustment_engine = adjustment_engine or PriceAdjustmentEngine()
        self.apply_price_adjustments = config.apply_price_adjustments
        self.fail_on_adjustment_error = config.fail_on_adjustment_error
        self.last_adjustment_reports: dict[str, AdjustmentReport] = {}

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
            logger.error(f"Data quality checks failed for {symbol}")
            raise DataQualityError(f"Data quality checks failed for {symbol}. Critical: {report.has_critical()}, Errors: {report.error_count()}")

        return mdf


    def get_last_cleaning_report(self, symbol: str) -> Any | None:
        return self.last_cleaning_reports.get(symbol)

    def get_last_adjustment_report(self, symbol: str) -> AdjustmentReport | None:
        return self.last_adjustment_reports.get(symbol)

    def _apply_adjustment(self, mdf: MarketDataFrame, symbol: str) -> MarketDataFrame:
        if not self.apply_price_adjustments or not self.adjustment_engine:
            return mdf

        try:
            adj_result = self.adjustment_engine.adjust_market_data(mdf)
            self.last_adjustment_reports[symbol] = adj_result.report
            return adj_result.market_data
        except Exception as e:
            if self.fail_on_adjustment_error:
                raise e
            logger.warning(f"Price adjustment failed for {symbol}: {e}")
            return mdf


    def _apply_cleaning(self, mdf: MarketDataFrame, symbol: str) -> MarketDataFrame:
        if not self.clean_data or not self.cleaner:
            return mdf

        try:
            cleaned_result = self.cleaner.clean_market_data(mdf)
            self.last_cleaning_reports[symbol] = cleaned_result.report
            return cleaned_result.market_data
        except Exception as e:
            if self.fail_on_cleaning_error:
                raise e
            logger.warning(f"Data cleaning failed for {symbol}: {e}")
            return mdf

    def get_last_quality_report(self, symbol: str) -> DataQualityReport | None:
        return self.last_quality_reports.get(symbol)

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: Timeframe = Timeframe.DAILY,
        period: str = "2y",
        refresh: bool = False,
        save: bool = True,
        allow_provider_fallback: bool = True,
    ) -> MarketDataFrame:
        """Fetch historical data for a single symbol, utilizing local storage if available and preferred."""
        self._validate_symbol(symbol)

        # Check local storage if preferred and refresh not requested
        if self.store and self.prefer_local and not refresh:
            if self.store.exists(symbol, self.provider.vendor, timeframe):
                logger.info(f"Reading {symbol} from local store.")
                try:
                    mdf = self.store.read_ohlcv(symbol, self.provider.vendor, timeframe)
                    return self._apply_quality_check(mdf, symbol)
                except Exception as e:
                    if not allow_provider_fallback:
                        raise
                    logger.warning(f"Failed to read local data for {symbol}, falling back to provider: {e}", exc_info=True)

        if not allow_provider_fallback:
            raise FileNotFoundError(
                f"No readable local data found for {symbol} ({timeframe.value}); provider fallback is disabled."
            )

        logger.info(f"Fetching {symbol} from provider ({self.provider.vendor.value}).")
        mdf = self.provider.fetch_one(
            symbol=symbol,
            timeframe=timeframe,
            period=period
        )


        mdf.validate_schema()
        mdf = self._apply_cleaning(mdf, symbol)
        mdf = self._apply_adjustment(mdf, symbol)
        mdf = self._apply_quality_check(mdf, symbol)

        if self.store and save:
            logger.info(f"Saving {symbol} to local store.")
            self.store.write_ohlcv(mdf)

        return mdf

    def get_many_ohlcv(
        self,
        symbols: list[str],
        timeframe: Timeframe = Timeframe.DAILY,
        period: str = "2y",
        refresh: bool = False,
        save: bool = True,
        allow_provider_fallback: bool = True,
    ) -> dict[str, MarketDataFrame]:
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
                        logger.debug(f"Read {sym} from local store.")
                        continue
                    except Exception as e:
                        if not allow_provider_fallback:
                            logger.warning(f"Failed to read local data for {sym}; provider fallback is disabled: {e}")
                            continue
                        logger.warning(f"Failed to read local data for {sym}, will fetch: {e}")

            if not allow_provider_fallback:
                continue
            symbols_to_fetch.append(sym)

        if symbols_to_fetch:
            logger.info(f"Fetching {len(symbols_to_fetch)} symbols from provider.")
            req = DataFetchRequest(
                symbols=symbols_to_fetch,
                timeframe=timeframe,
                period=period
            )

            provider_results = self.provider.fetch_ohlcv(req)

            for sym, mdf in provider_results.items():

                mdf.validate_schema()
                mdf = self._apply_cleaning(mdf, sym)
                mdf = self._apply_adjustment(mdf, sym)
                mdf = self._apply_quality_check(mdf, sym)
                results[sym] = mdf

                if self.store and save:
                    self.store.write_ohlcv(mdf)
                    logger.debug(f"Saved {sym} to local store.")

        return results

    def provider_status(self) -> dict[str, Any]:
        """Return the current status of the configured data provider and storage."""
        data_dir = None
        if self.store and self.store.settings:
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

    # --- Phase 51: Data Provider V2 Methods ---

    def fetch_v2(self, request: 'ProviderRequest') -> 'ProviderResponse':
        """Fetch data using the V2 architecture with fallback routing."""
        from bist_signal_bot.data.providers_v2.fallback import FallbackProviderRouter
        from bist_signal_bot.data.providers_v2.local_file import LocalFileProvider
        from bist_signal_bot.data.providers_v2.yfinance_provider import YFinanceProviderV2
        from bist_signal_bot.data.providers_v2.lineage import DataLineageStore
        from bist_signal_bot.data.providers_v2.health import ProviderHealthTracker
        from bist_signal_bot.storage.market_store import MarketStore

        providers = [LocalFileProvider()]

        # Only add yfinance if network is allowed by config and request
        if getattr(self.settings, "DATA_YFINANCE_ENABLED", True):
             providers.append(YFinanceProviderV2())

        router = FallbackProviderRouter(providers, self.settings)

        # Fire audit event
        from bist_signal_bot.core.audit import AuditEvent, AuditEventType
        if getattr(self, "audit_logger", None):
            event = AuditEvent(event_type=AuditEventType("DATA_PROVIDER_V2_FETCH_STARTED"), message="system", metadata={"request": request.model_dump()})
            self.audit_logger.log(event)

        response = router.fetch(request)

        # Save to store and lineage if fetched
        if getattr(self.settings, "SAVE_FETCHED_DATA", True):
             store = MarketStore(self.settings)
             lineage_store = DataLineageStore(self.settings) if getattr(self.settings, "DATA_PROVIDER_RECORD_LINEAGE", True) else None

             for symbol, data in response.data_by_symbol.items():
                 # Find lineage
                 lin = next((l for l in response.lineage if l.symbol == symbol), None)

                 # Only save if we actually fetched from network (to avoid re-saving local reads)
                 # Or if explicitly overwriting cache. For simplicity, just save network reads.
                 if lin and lin.provider_type != getattr(self, "ProviderType", None) and lin.provider_name != "Local File Provider":
                      store.save_ohlcv(symbol, request.timeframe, data)
                      if lineage_store:
                          lineage_store.append(lin)

        # Record Health
        if getattr(self.settings, "DATA_PROVIDER_RECORD_HEALTH", True):
             health_tracker = ProviderHealthTracker(self.settings)
             for snap in router.healthcheck_all():
                  health_tracker.record_snapshot(snap)

        if getattr(self, "audit_logger", None):
            event = AuditEvent(event_type=AuditEventType("DATA_PROVIDER_V2_FETCH_COMPLETED"), message="system", metadata={"status": response.status.value})
            self.audit_logger.log(event)

        return response

    def update_incremental(self, symbols: list[str], timeframe: str, provider_order: list[str] | None = None) -> 'ProviderResponse':
        from bist_signal_bot.data.incremental import IncrementalUpdatePlanner
        from bist_signal_bot.data.providers_v2.models import ProviderRequest, ProviderType
        from bist_signal_bot.storage.market_store import MarketStore
        from bist_signal_bot.data.providers_v2.lineage import DataLineageStore

        store = MarketStore(self.settings)
        planner = IncrementalUpdatePlanner()
        order = [ProviderType(p.strip().upper()) for p in provider_order] if provider_order else []

        # We need to construct sub-requests based on what's missing
        all_data = {}
        all_lineage = []

        from bist_signal_bot.core.audit import AuditEvent, AuditEventType
        if getattr(self, "audit_logger", None):
            event = AuditEvent(event_type=AuditEventType("DATA_INCREMENTAL_UPDATE_PLANNED"), message="system", metadata={"symbols": symbols})
            self.audit_logger.log(event)

        for sym in symbols:
            local_data = store.load_ohlcv(sym, timeframe)
            plan = planner.plan_update(sym, timeframe, local_data)

            if plan["action"] == "SKIP":
                all_data[sym] = local_data
                continue

            req = ProviderRequest(
                symbols=[sym],
                timeframe=timeframe,
                start_date=plan["start_date"],
                end_date=plan["end_date"],
                allow_network=True,
                provider_order=order
            )

            res = self.fetch_v2(req)
            if sym in res.data_by_symbol:
                new_data = res.data_by_symbol[sym]
                merged = planner.merge_incremental_data(local_data, new_data)
                all_data[sym] = merged

                # Update store
                lineage = next((l for l in res.lineage if l.symbol == sym), None)
                if lineage:
                    all_lineage.append(lineage)
                    store.save_ohlcv(sym, timeframe, merged, lineage)
                    if getattr(self.settings, "DATA_PROVIDER_RECORD_LINEAGE", True):
                         DataLineageStore(self.settings).append(lineage)

        if getattr(self, "audit_logger", None):
            event = AuditEvent(event_type=AuditEventType("DATA_INCREMENTAL_UPDATE_COMPLETED"), message="system")
            self.audit_logger.log(event)

        from bist_signal_bot.data.providers_v2.models import ProviderResponse, DataFetchStatus
        return ProviderResponse(
            request=ProviderRequest(symbols=symbols, timeframe=timeframe),
            status=DataFetchStatus.SUCCESS,
            data_by_symbol=all_data,
            lineage=all_lineage
        )

    def import_market_data(self, request: 'ImportRequest') -> 'ImportResult':
        from bist_signal_bot.data.providers_v2.models import ImportResult, DataImportStatus
        from bist_signal_bot.storage.market_store import MarketStore
        from bist_signal_bot.data.providers_v2.lineage import DataLineageStore

        path = str(request.input_path).lower()
        if path.endswith('.csv'):
             from bist_signal_bot.data.importers.csv_importer import CSVMarketDataImporter
             importer = CSVMarketDataImporter()
        elif path.endswith('.parquet'):
             from bist_signal_bot.data.importers.parquet_importer import ParquetMarketDataImporter
             importer = ParquetMarketDataImporter()
        else:
             return ImportResult(request=request, status=DataImportStatus.FAILED, symbol=request.symbol or "UNKNOWN", timeframe=request.timeframe, errors=["Unsupported file format."])

        from bist_signal_bot.core.audit import AuditEvent, AuditEventType
        if getattr(self, "audit_logger", None):
            event = AuditEvent(event_type=AuditEventType("DATA_IMPORT_STARTED"), message="system", metadata={"path": request.input_path})
            self.audit_logger.log(event)

        res = importer.import_file(request)

        if res.status == DataImportStatus.IMPORTED and request.save_to_cache:
            df = res.metadata.get("_parsed_df")
            if df is not None:
                store = MarketStore(self.settings)
                out_path = store.save_ohlcv(res.symbol, res.timeframe, df, res.lineage)
                res.output_path = str(out_path)

                if res.lineage and getattr(self.settings, "DATA_PROVIDER_RECORD_LINEAGE", True):
                     DataLineageStore(self.settings).append(res.lineage)

        if getattr(self, "audit_logger", None):
            event_type = AuditEventType("DATA_IMPORT_COMPLETED") if res.status == DataImportStatus.IMPORTED else AuditEventType("DATA_IMPORT_FAILED")
            event = AuditEvent(event_type=event_type, message="system", metadata={"status": res.status.value})
            self.audit_logger.log(event)

        # Cleanup metadata before returning
        if "_parsed_df" in res.metadata:
            del res.metadata["_parsed_df"]

        return res

    def freshness_report(self, symbols: list[str], timeframe: str, max_age_hours: float) -> 'FreshnessReport':
        from bist_signal_bot.data.freshness import DataFreshnessChecker
        from bist_signal_bot.core.audit import AuditEvent, AuditEventType

        if getattr(self, "audit_logger", None):
            event = AuditEvent(event_type=AuditEventType("DATA_FRESHNESS_CHECKED"), message="system", metadata={"symbols": len(symbols)})
            self.audit_logger.log(event)

        checker = DataFreshnessChecker()
        return checker.check_symbols(symbols, timeframe, max_age_hours)

    def compare_sources(self, symbol: str, timeframe: str, left_source: str, right_source: str) -> 'DataComparisonReport':
        from bist_signal_bot.data.comparison import MarketDataComparator
        from bist_signal_bot.data.providers_v2.models import DataComparisonRequest
        from bist_signal_bot.data.providers_v2.models import ProviderRequest, ProviderType

        # Helper to fetch data for comparison
        def get_source_data(src: str):
             req = ProviderRequest(symbols=[symbol], timeframe=timeframe, provider_order=[ProviderType(src.upper())])
             res = self.fetch_v2(req)
             return res.data_by_symbol.get(symbol)

        left_df = get_source_data(left_source)
        right_df = get_source_data(right_source)

        from bist_signal_bot.core.audit import AuditEvent, AuditEventType
        if getattr(self, "audit_logger", None):
            event = AuditEvent(event_type=AuditEventType("DATA_SOURCE_COMPARED"), message="system", metadata={"symbol": symbol})
            self.audit_logger.log(event)

        comp = MarketDataComparator()
        req = DataComparisonRequest(
            symbol=symbol,
            timeframe=timeframe,
            left=left_df,
            right=right_df,
            left_source=left_source,
            right_source=right_source,
            close_tolerance_pct=getattr(self.settings, "DATA_COMPARE_CLOSE_TOLERANCE_PCT", 0.10),
            volume_tolerance_pct=getattr(self.settings, "DATA_COMPARE_VOLUME_TOLERANCE_PCT", 5.0)
        )
        return comp.compare(req)

    def lineage_summary(self, symbol: str | None = None) -> dict[str, Any]:
        from bist_signal_bot.data.providers_v2.lineage import DataLineageStore
        store = DataLineageStore(self.settings)
        return store.lineage_summary(symbol)
