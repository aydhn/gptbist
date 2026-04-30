import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.logging_setup import sanitize_for_logging


class AuditEventType(str, Enum):
    APP_START = "APP_START"
    APP_STOP = "APP_STOP"
    HEALTHCHECK = "HEALTHCHECK"
    DATA_FETCH = "DATA_FETCH"
    DATA_DOWNLOAD_START = "DATA_DOWNLOAD_START"
    DATA_DOWNLOAD_SYMBOL = "DATA_DOWNLOAD_SYMBOL"
    DATA_DOWNLOAD_FINISHED = "DATA_DOWNLOAD_FINISHED"
    DATA_CACHE_READ = "DATA_CACHE_READ"
    DATA_CACHE_WRITE = "DATA_CACHE_WRITE"
    DATA_QUALITY_CHECK = "DATA_QUALITY_CHECK"
    SIGNAL_GENERATED = "SIGNAL_GENERATED"
    BACKTEST_RUN = "BACKTEST_RUN"
    OPTIMIZER_RUN = "OPTIMIZER_RUN"
    ML_TRAINING_RUN = "ML_TRAINING_RUN"
    TELEGRAM_SENT = "TELEGRAM_SENT"
    ERROR = "ERROR"
    CONFIG_LOADED = "CONFIG_LOADED"
    SYSTEM = "SYSTEM"
    CLI_COMMAND = "CLI_COMMAND"
    UNIVERSE_INIT = "UNIVERSE_INIT"
    TREND_FEATURE_CALCULATION = "TREND_FEATURE_CALCULATION"
    MOMENTUM_FEATURE_CALCULATION = "MOMENTUM_FEATURE_CALCULATION"
    UNIVERSE_VALIDATE = "UNIVERSE_VALIDATE"
    UNIVERSE_ADD_SYMBOL = "UNIVERSE_ADD_SYMBOL"
    UNIVERSE_REMOVE_SYMBOL = "UNIVERSE_REMOVE_SYMBOL"
    UNIVERSE_ACTIVATE_SYMBOL = "UNIVERSE_ACTIVATE_SYMBOL"
    UNIVERSE_DEACTIVATE_SYMBOL = "UNIVERSE_DEACTIVATE_SYMBOL"
    UNIVERSE_IMPORT = "UNIVERSE_IMPORT"
    UNIVERSE_EXPORT = "UNIVERSE_EXPORT"
    UNIVERSE_SNAPSHOT = "UNIVERSE_SNAPSHOT"
    WATCHLIST_UPDATE = "WATCHLIST_UPDATE"

    CORPORATE_ACTIONS_INIT = "CORPORATE_ACTIONS_INIT"
    CORPORATE_ACTIONS_IMPORT = "CORPORATE_ACTIONS_IMPORT"
    CORPORATE_ACTIONS_EXPORT = "CORPORATE_ACTIONS_EXPORT"
    CORPORATE_ACTIONS_ADD = "CORPORATE_ACTIONS_ADD"
    CORPORATE_ACTIONS_REMOVE = "CORPORATE_ACTIONS_REMOVE"
    CORPORATE_ACTIONS_VALIDATE = "CORPORATE_ACTIONS_VALIDATE"
    DATA_ADJUSTMENT = "DATA_ADJUSTMENT"


@dataclass
class AuditEvent:
    event_type: AuditEventType
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    level: str = "INFO"
    symbol: str | None = None
    run_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.message:
            raise ValueError("Audit event message cannot be empty")
        if self.symbol:
            self.symbol = self.symbol.upper()

class AuditLogger:
    def __init__(self, settings: Settings, logger: logging.Logger | None = None):
        self.settings = settings
        self._enabled = settings.ENABLE_AUDIT_LOG
        self._logger = logger or logging.getLogger("bist_signal_bot.audit")

        if self._enabled:
            log_dir = Path(settings.LOG_DIR)
            log_dir.mkdir(parents=True, exist_ok=True)
            self._audit_file = log_dir / settings.AUDIT_LOG_FILE_NAME
        else:
            self._audit_file = None

    def log_event(self, event: AuditEvent) -> None:
        if not self._enabled or not self._audit_file:
            return

        try:
            sanitized_metadata = sanitize_for_logging(event.metadata, mask_secrets=self.settings.MASK_SECRETS_IN_LOGS)

            event_dict = {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "level": event.level,
                "message": event.message,
                "symbol": event.symbol,
                "run_id": event.run_id,
                "metadata": sanitized_metadata
            }

            # JSON Lines format
            with open(self._audit_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_dict, ensure_ascii=False) + "\n")

        except Exception as e:
            # Fallback to standard logger if audit logging fails
            self._logger.error(f"Failed to write to audit log: {e}")

    def log_app_start(self, run_id: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        self.log_event(AuditEvent(
            event_type=AuditEventType.APP_START,
            message="Application started",
            run_id=run_id,
            metadata=metadata or {}
        ))

    def log_healthcheck(self, summary: dict[str, Any], run_id: str | None = None) -> None:
        self.log_event(AuditEvent(
            event_type=AuditEventType.HEALTHCHECK,
            message="Healthcheck executed",
            run_id=run_id,
            metadata=summary
        ))

    def log_data_fetch(self, symbol: str, provider: str, timeframe: str, run_id: str | None = None, metadata: dict[str, Any] | None = None) -> None:
        md = {"provider": provider, "timeframe": timeframe}
        if metadata:
            md.update(metadata)
        self.log_event(AuditEvent(
            event_type=AuditEventType.DATA_FETCH,
            message=f"Fetched data for {symbol}",
            symbol=symbol,
            run_id=run_id,
            metadata=md
        ))

    def log_cache_read(self, symbol: str, vendor: str, timeframe: str, run_id: str | None = None) -> None:
        self.log_event(AuditEvent(
            event_type=AuditEventType.DATA_CACHE_READ,
            message=f"Read {symbol} from cache",
            symbol=symbol,
            run_id=run_id,
            metadata={"vendor": vendor, "timeframe": timeframe}
        ))

    def log_cache_write(self, symbol: str, vendor: str, timeframe: str, row_count: int, run_id: str | None = None) -> None:
        self.log_event(AuditEvent(
            event_type=AuditEventType.DATA_CACHE_WRITE,
            message=f"Wrote {symbol} to cache",
            symbol=symbol,
            run_id=run_id,
            metadata={"vendor": vendor, "timeframe": timeframe, "row_count": row_count}
        ))

    def log_error(self, error: Exception, context: dict[str, Any] | None = None, run_id: str | None = None) -> None:
        self.log_event(AuditEvent(
            event_type=AuditEventType.ERROR,
            message=str(error),
            level="ERROR",
            run_id=run_id,
            metadata={"error_type": type(error).__name__, "context": context or {}}
        ))

    def log_universe_update(self, event_type: AuditEventType, message: str, action: str, symbols_affected: list[str], file_path: str | None = None, validation_passed: bool | None = None, issue_count: int | None = None, run_id: str | None = None) -> None:
        metadata = {
            "action": action,
            "symbols_affected": symbols_affected,
            "file_path": file_path,
        }
        if validation_passed is not None:
            metadata["validation_passed"] = validation_passed
        if issue_count is not None:
            metadata["issue_count"] = issue_count

        self.log_event(AuditEvent(
            event_type=event_type,
            message=message,
            run_id=run_id,
            metadata=metadata
        ))

    def log_indicator_calculation(self, symbol: str, timeframe: str, indicators: list[str], success_count: int, failed_count: int, elapsed_seconds: float, run_id: str | None = None) -> None:
        self.log_event(AuditEvent(
            event_type=AuditEventType.CLI_COMMAND,
            message=f"Calculated indicators for {symbol}",
            symbol=symbol,
            run_id=run_id,
            metadata={
                "timeframe": timeframe,
                "indicators_requested": indicators,
                "success_count": success_count,
                "failed_count": failed_count,
                "elapsed_seconds": elapsed_seconds
            }
        ))
