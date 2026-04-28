from typing import Any
import logging
from datetime import datetime, UTC

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.audit import AuditEvent, AuditEventType, AuditLogger
from bist_signal_bot.core.exceptions import DataProviderError, SymbolUniverseError
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.data.models import (
    BatchDownloadResult,
    DownloadStatus,
    SymbolDownloadResult,
    Timeframe,
)
from bist_signal_bot.data.symbol_universe import SymbolGroup, SymbolUniverse
from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol

logger = logging.getLogger("bist_signal_bot.data.downloader")

class MarketDataDownloader:
    """
    Downloads OHLCV data for symbols, utilizing MarketDataService,
    LocalMarketDataStore, and DataQualityChecker.
    """

    def __init__(
        self,
        data_service: MarketDataService,
        universe: SymbolUniverse,
        settings: Settings,
        audit_logger: AuditLogger | None = None,
        notifier: Any | None = None,  # TelegramNotifier or MockNotifier
        logger: logging.Logger | None = None
    ):
        self.data_service = data_service
        self.universe = universe
        self.settings = settings
        self.audit_logger = audit_logger
        self.notifier = notifier
        self._logger = logger or logging.getLogger("bist_signal_bot.downloader")

    def download_symbol(
        self,
        symbol: str,
        timeframe: Timeframe = Timeframe.DAILY,
        period: str | None = None,
        refresh: bool = False,
        save: bool = True
    ) -> SymbolDownloadResult:
        start_time = datetime.now(UTC)

        try:
            symbol = ensure_valid_internal_symbol(symbol)
        except Exception as e:
            return SymbolDownloadResult(
                symbol=symbol, status=DownloadStatus.FAILED, row_count=0,
                source="unknown", timeframe=timeframe.value, saved=False, from_cache=False,
                error=str(e), elapsed_seconds=0.0
            )

        if not self.universe.contains(symbol):
            return SymbolDownloadResult(
                symbol=symbol, status=DownloadStatus.FAILED, row_count=0,
                source="unknown", timeframe=timeframe.value, saved=False, from_cache=False,
                error=f"Symbol '{symbol}' not found in Universe.", elapsed_seconds=0.0
            )

        eff_period = period or self.settings.DOWNLOAD_DEFAULT_PERIOD

        if self.audit_logger:
            self.audit_logger.log_event(AuditEvent(
                event_type=AuditEventType.DATA_DOWNLOAD_SYMBOL,
                message=f"Starting download for {symbol}",
                symbol=symbol,
                metadata={"timeframe": timeframe.value, "period": eff_period, "refresh": refresh, "save": save}
            ))

        try:
            mdf = self.data_service.get_ohlcv(symbol, timeframe=timeframe, period=eff_period, refresh=refresh, save=save)

            end_time = datetime.now(UTC)
            elapsed = (end_time - start_time).total_seconds()

            # Extract metadata set by store/provider
            from_cache = mdf.metadata.get("from_cache", False)
            saved = mdf.metadata.get("saved_to_store", False) if save else False
            file_path = mdf.metadata.get("storage_path", None)

            quality_score = None
            quality_passed = None
            if mdf.quality_report:
                quality_score = mdf.quality_report.score
                quality_passed = mdf.quality_report.passed


            s_start = None
            s_end = None
            if not mdf.data.empty and len(mdf.data.index) > 0:
                try:
                    s_start = mdf.data.index.min().to_pydatetime()
                    s_end = mdf.data.index.max().to_pydatetime()
                except Exception:
                    pass


            return SymbolDownloadResult(
                symbol=symbol,
                status=DownloadStatus.SUCCESS,
                row_count=mdf.row_count(),
                start=s_start,
                end=s_end,
                source=mdf.source.value,
                timeframe=timeframe.value,
                saved=saved,
                from_cache=from_cache,
                quality_score=quality_score,
                quality_passed=quality_passed,
                error=None,
                file_path=file_path,
                elapsed_seconds=elapsed
            )

        except Exception as e:
            self._logger.error(f"Download failed for {symbol}: {e}")
            end_time = datetime.now(UTC)
            elapsed = (end_time - start_time).total_seconds()
            return SymbolDownloadResult(
                symbol=symbol,
                status=DownloadStatus.FAILED,
                row_count=0,
                source="unknown",
                timeframe=timeframe.value,
                saved=False,
                from_cache=False,
                error=str(e),
                elapsed_seconds=elapsed
            )

    def download_symbols(
        self,
        symbols: list[str],
        timeframe: Timeframe = Timeframe.DAILY,
        period: str | None = None,
        refresh: bool = False,
        save: bool = True,
        continue_on_error: bool = True
    ) -> BatchDownloadResult:
        start_time = datetime.now(UTC)

        try:
            symbols = [ensure_valid_internal_symbol(s) for s in symbols]
        except Exception as e:
            if not continue_on_error:
                raise DataProviderError(f"Invalid symbol in batch: {e}")
            # If continue on error, we just keep the raw names, download_symbol will catch them

        unique_symbols = list(dict.fromkeys(symbols))

        eff_period = period or self.settings.DOWNLOAD_DEFAULT_PERIOD

        if self.audit_logger:
            self.audit_logger.log_event(AuditEvent(
                event_type=AuditEventType.DATA_DOWNLOAD_START,
                message=f"Starting batch download for {len(unique_symbols)} symbols",
                metadata={"count": len(unique_symbols), "timeframe": timeframe.value, "period": eff_period}
            ))

        results = []
        for sym in unique_symbols:
            res = self.download_symbol(sym, timeframe, eff_period, refresh, save)
            results.append(res)
            if res.status == DownloadStatus.FAILED and not continue_on_error:
                break

        end_time = datetime.now(UTC)
        elapsed = (end_time - start_time).total_seconds()

        success = sum(1 for r in results if r.status == DownloadStatus.SUCCESS)
        failed = sum(1 for r in results if r.status == DownloadStatus.FAILED)

        batch_result = BatchDownloadResult(
            requested_count=len(unique_symbols),
            success_count=success,
            failed_count=failed,
            skipped_count=0,
            partial_count=0,
            results=results,
            started_at=start_time,
            finished_at=end_time,
            elapsed_seconds=elapsed,
            provider=self.data_service.provider.vendor.value,
            timeframe=timeframe.value,
            period=eff_period,
            refresh=refresh,
            save=save
        )

        if self.audit_logger:
            self.audit_logger.log_event(AuditEvent(
                event_type=AuditEventType.DATA_DOWNLOAD_FINISHED,
                message=f"Finished batch download for {len(unique_symbols)} symbols",
                metadata=batch_result.summary()
            ))

        return batch_result

    def download_universe(
        self,
        group: SymbolGroup | None = None,
        active_only: bool = True,
        timeframe: Timeframe = Timeframe.DAILY,
        period: str | None = None,
        refresh: bool = False,
        save: bool = True
    ) -> BatchDownloadResult:
        if group:
            symbols = [s.symbol for s in self.universe.filter_by_group(group)]
        else:
            symbols = self.universe.list_symbols(active_only=active_only)

        continue_on_error = self.settings.DOWNLOAD_CONTINUE_ON_ERROR

        return self.download_symbols(symbols, timeframe, period, refresh, save, continue_on_error)

    def send_download_summary(self, result: BatchDownloadResult) -> None:
        if not self.notifier:
            return

        try:
            from bist_signal_bot.notifications.formatter import NotificationFormatter
            formatter = NotificationFormatter()
            message = formatter.format_download_summary(result)
            self.notifier.send_message(message)
        except Exception as e:
            self._logger.warning(f"Failed to send download summary telegram: {e}")

from typing import Any
