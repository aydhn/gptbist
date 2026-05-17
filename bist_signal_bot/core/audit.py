import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.security.redaction import SecretRedactor


class AuditEventType(str, Enum):
    SCENARIO_RUN_STARTED = "SCENARIO_RUN_STARTED"
    SCENARIO_RUN_COMPLETED = "SCENARIO_RUN_COMPLETED"
    SCENARIO_RUN_FAILED = "SCENARIO_RUN_FAILED"
    SCENARIO_STEP_COMPLETED = "SCENARIO_STEP_COMPLETED"
    SCENARIO_GOLDEN_COMPARED = "SCENARIO_GOLDEN_COMPARED"
    SCENARIO_GOLDEN_UPDATED = "SCENARIO_GOLDEN_UPDATED"
    SCENARIO_VALIDATED = "SCENARIO_VALIDATED"
    SCENARIO_SANDBOX_CLEANED = "SCENARIO_SANDBOX_CLEANED"
    # Release Manager (Phase 50)
    RELEASE_CHECK_STARTED = "RELEASE_CHECK_STARTED"
    RELEASE_CHECK_COMPLETED = "RELEASE_CHECK_COMPLETED"
    RELEASE_READINESS_STARTED = "RELEASE_READINESS_STARTED"
    RELEASE_READINESS_COMPLETED = "RELEASE_READINESS_COMPLETED"
    RELEASE_READINESS_FAILED = "RELEASE_READINESS_FAILED"
    RELEASE_REHEARSAL_STARTED = "RELEASE_REHEARSAL_STARTED"
    RELEASE_REHEARSAL_COMPLETED = "RELEASE_REHEARSAL_COMPLETED"
    RELEASE_CANDIDATE_STARTED = "RELEASE_CANDIDATE_STARTED"
    RELEASE_CANDIDATE_CREATED = "RELEASE_CANDIDATE_CREATED"
    RELEASE_CANDIDATE_FAILED = "RELEASE_CANDIDATE_FAILED"
    RELEASE_NOTES_CREATED = "RELEASE_NOTES_CREATED"
    RELEASE_BLOCKER_FOUND = "RELEASE_BLOCKER_FOUND"
    RELEASE_REPORT_SAVED = "RELEASE_REPORT_SAVED"


    REPORT_GENERATION_STARTED = "report_generation_started"
    REPORT_GENERATION_COMPLETED = "report_generation_completed"
    REPORT_GENERATION_FAILED = "report_generation_failed"
    REPORT_EXPORTED = "report_exported"
    REPORT_DIGEST_CREATED = "report_digest_created"
    REPORT_DIGEST_SENT = "report_digest_sent"
    REPORT_DIGEST_FAILED = "report_digest_failed"
    REPORT_SECURITY_BLOCKED = "report_security_blocked"
    REPORT_SAVED = "report_saved"
    PERFORMANCE_RESOURCE_SNAPSHOT = "PERFORMANCE_RESOURCE_SNAPSHOT"
    PERFORMANCE_PROFILE_STARTED = "PERFORMANCE_PROFILE_STARTED"
    PERFORMANCE_PROFILE_COMPLETED = "PERFORMANCE_PROFILE_COMPLETED"
    PERFORMANCE_BENCHMARK_STARTED = "PERFORMANCE_BENCHMARK_STARTED"
    PERFORMANCE_BENCHMARK_COMPLETED = "PERFORMANCE_BENCHMARK_COMPLETED"
    PERFORMANCE_CACHE_SCANNED = "PERFORMANCE_CACHE_SCANNED"
    PERFORMANCE_CACHE_CLEANUP_DRY_RUN = "PERFORMANCE_CACHE_CLEANUP_DRY_RUN"
    PERFORMANCE_CACHE_CLEANUP_EXECUTED = "PERFORMANCE_CACHE_CLEANUP_EXECUTED"
    PERFORMANCE_REPORT_SAVED = "PERFORMANCE_REPORT_SAVED"
    PERFORMANCE_BATCH_RECOMMENDED = "PERFORMANCE_BATCH_RECOMMENDED"

    DOCS_GENERATION_STARTED = "DOCS_GENERATION_STARTED"
    DOCS_GENERATION_COMPLETED = "DOCS_GENERATION_COMPLETED"
    DOCS_GENERATION_FAILED = "DOCS_GENERATION_FAILED"
    DOCS_VALIDATION_STARTED = "DOCS_VALIDATION_STARTED"
    DOCS_VALIDATION_COMPLETED = "DOCS_VALIDATION_COMPLETED"
    DOCS_VALIDATION_FAILED = "DOCS_VALIDATION_FAILED"
    DOCS_COMMAND_CATALOG_BUILT = "DOCS_COMMAND_CATALOG_BUILT"
    DOCS_RUNBOOKS_GENERATED = "DOCS_RUNBOOKS_GENERATED"
    DOCS_EXAMPLES_VALIDATED = "DOCS_EXAMPLES_VALIDATED"
    DOCS_REPORT_SAVED = "DOCS_REPORT_SAVED"

    PACKAGING_DOCTOR_RUN = "PACKAGING_DOCTOR_RUN"
    PACKAGING_DEPENDENCY_CHECK_RUN = "PACKAGING_DEPENDENCY_CHECK_RUN"
    PACKAGING_INSTALLERS_GENERATED = "PACKAGING_INSTALLERS_GENERATED"
    PACKAGING_MANIFEST_CREATED = "PACKAGING_MANIFEST_CREATED"
    PACKAGING_RELEASE_STARTED = "PACKAGING_RELEASE_STARTED"
    PACKAGING_RELEASE_COMPLETED = "PACKAGING_RELEASE_COMPLETED"
    PACKAGING_RELEASE_FAILED = "PACKAGING_RELEASE_FAILED"
    PACKAGING_SECRET_BLOCKED = "PACKAGING_SECRET_BLOCKED"
    PACKAGING_ZIP_CREATED = "PACKAGING_ZIP_CREATED"

    ML_TRAINING_STARTED = "ML_TRAINING_STARTED"
    ML_TRAINING_COMPLETED = "ML_TRAINING_COMPLETED"
    ML_TRAINING_FAILED = "ML_TRAINING_FAILED"
    ML_INFERENCE_STARTED = "ML_INFERENCE_STARTED"
    ML_INFERENCE_COMPLETED = "ML_INFERENCE_COMPLETED"
    ML_INFERENCE_FAILED = "ML_INFERENCE_FAILED"
    ML_SIGNAL_FILTER_APPLIED = "ML_SIGNAL_FILTER_APPLIED"
    ML_SIGNAL_REJECTED = "ML_SIGNAL_REJECTED"
    ML_SIGNAL_SCORE_ADJUSTED = "ML_SIGNAL_SCORE_ADJUSTED"
    ML_FEATURE_ALIGNMENT_FAILED = "ML_FEATURE_ALIGNMENT_FAILED"
    ML_MODEL_SAVED = "ML_MODEL_SAVED"
    ML_MODEL_LOADED = "ML_MODEL_LOADED"
    ML_PREDICTION_RUN = "ML_PREDICTION_RUN"
    ML_MODEL_DELETED = "ML_MODEL_DELETED"

    PORTFOLIO_RISK_EVALUATED = "PORTFOLIO_RISK_EVALUATED"
    PORTFOLIO_ALLOCATION_CALCULATED = "PORTFOLIO_ALLOCATION_CALCULATED"
    PORTFOLIO_CORRELATION_CALCULATED = "PORTFOLIO_CORRELATION_CALCULATED"
    PORTFOLIO_EXPOSURE_CALCULATED = "PORTFOLIO_EXPOSURE_CALCULATED"
    PORTFOLIO_SIGNAL_REJECTED = "PORTFOLIO_SIGNAL_REJECTED"
    PAPER_ACCOUNT_INITIALIZED = "PAPER_ACCOUNT_INITIALIZED"
    PAPER_ACCOUNT_RESET = "PAPER_ACCOUNT_RESET"
    PAPER_RUN_ONCE = "PAPER_RUN_ONCE"
    PAPER_ORDER_CREATED = "PAPER_ORDER_CREATED"
    PAPER_ORDER_REJECTED = "PAPER_ORDER_REJECTED"
    PAPER_FILL_SIMULATED = "PAPER_FILL_SIMULATED"
    PAPER_POSITION_OPENED = "PAPER_POSITION_OPENED"
    PAPER_POSITION_CLOSED = "PAPER_POSITION_CLOSED"
    PAPER_MARK_TO_MARKET = "PAPER_MARK_TO_MARKET"
    PAPER_LEDGER_SAVED = "PAPER_LEDGER_SAVED"
    SCAN_STARTED = "SCAN_STARTED"
    SCAN_COMPLETED = "SCAN_COMPLETED"
    SCAN_SYMBOL_PROCESSED = "SCAN_SYMBOL_PROCESSED"
    SCAN_SYMBOL_FAILED = "SCAN_SYMBOL_FAILED"
    SCAN_REPORT_WRITTEN = "SCAN_REPORT_WRITTEN"
    SCAN_TELEGRAM_SENT = "SCAN_TELEGRAM_SENT"
    SCAN_PAPER_SIMULATION_REQUESTED = "SCAN_PAPER_SIMULATION_REQUESTED"


    SECURITY_AUDIT_RUN = "SECURITY_AUDIT_RUN"
    SECURITY_PREFLIGHT_RUN = "SECURITY_PREFLIGHT_RUN"
    SECURITY_PREFLIGHT_FAILED = "SECURITY_PREFLIGHT_FAILED"
    SECRET_REDACTION_APPLIED = "SECRET_REDACTION_APPLIED"
    SECRET_LEAK_BLOCKED = "SECRET_LEAK_BLOCKED"
    FORBIDDEN_ACTION_BLOCKED = "FORBIDDEN_ACTION_BLOCKED"
    UNSAFE_CLAIM_SANITIZED = "UNSAFE_CLAIM_SANITIZED"
    KILL_SWITCH_ACTIVATED = "KILL_SWITCH_ACTIVATED"
    KILL_SWITCH_DEACTIVATED = "KILL_SWITCH_DEACTIVATED"
    KILL_SWITCH_BLOCKED_ACTION = "KILL_SWITCH_BLOCKED_ACTION"
    PATH_SECURITY_BLOCKED = "PATH_SECURITY_BLOCKED"

    PORTFOLIO_SIGNAL_APPROVED = "PORTFOLIO_SIGNAL_APPROVED"


    # Risk Engine Events
    RISK_DECISION_CREATED = "RISK_DECISION_CREATED"
    RISK_BATCH_EVALUATED = "RISK_BATCH_EVALUATED"
    POSITION_SIZE_CALCULATED = "POSITION_SIZE_CALCULATED"
    STOP_TARGET_CALCULATED = "STOP_TARGET_CALCULATED"
    RISK_SIGNAL_REJECTED = "RISK_SIGNAL_REJECTED"
    RISK_SIGNAL_APPROVED = "RISK_SIGNAL_APPROVED"

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
    VOLATILITY_FEATURE_CALCULATION = "VOLATILITY_FEATURE_CALCULATION"
    VOLUME_FEATURE_CALCULATION = "VOLUME_FEATURE_CALCULATION"
    PATTERN_FEATURE_CALCULATION = "PATTERN_FEATURE_CALCULATION"
    DIVERGENCE_DETECTION = "DIVERGENCE_DETECTION"


    STRATEGY_RUN = "STRATEGY_RUN"
    STRATEGY_BATCH_RUN = "STRATEGY_BATCH_RUN"
    SIGNAL_CANDIDATE_GENERATED = "SIGNAL_CANDIDATE_GENERATED"

    BENCHMARK_RUN = "BENCHMARK_RUN"
    BENCHMARK_BATCH_RUN = "BENCHMARK_BATCH_RUN"
    BENCHMARK_SIGNAL_GENERATED = "BENCHMARK_SIGNAL_GENERATED"

    COST_MODEL_CALCULATION = "COST_MODEL_CALCULATION"
    COST_SCENARIO_SELECTED = "COST_SCENARIO_SELECTED"



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
            sanitized_metadata = event.metadata
            if self.settings.SECURITY_REDACT_AUDIT:
                from bist_signal_bot.security.redaction import SecretRedactor
                sanitized_metadata = SecretRedactor.redact_dict(event.metadata)

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

    def log_cost_model_calculation(self, symbol: str, side: str, quantity: float, price: float, scenario: str, total_cost: float, total_cost_bps: float, run_id: str | None = None) -> None:
        self.log_event(AuditEvent(
            event_type=AuditEventType.COST_MODEL_CALCULATION,
            message="Cost model calculated",
            symbol=symbol,
            run_id=run_id,
            metadata={
                "side": side,
                "quantity": quantity,
                "price": price,
                "scenario": scenario,
                "total_cost": total_cost,
                "total_cost_bps": total_cost_bps
            }
        ))

RUNTIME_RUN_STARTED = "RUNTIME_RUN_STARTED"
RUNTIME_RUN_COMPLETED = "RUNTIME_RUN_COMPLETED"
RUNTIME_RUN_FAILED = "RUNTIME_RUN_FAILED"
RUNTIME_JOB_STARTED = "RUNTIME_JOB_STARTED"
RUNTIME_JOB_COMPLETED = "RUNTIME_JOB_COMPLETED"
RUNTIME_JOB_FAILED = "RUNTIME_JOB_FAILED"
RUNTIME_LOCK_ACQUIRED = "RUNTIME_LOCK_ACQUIRED"
RUNTIME_LOCK_RELEASED = "RUNTIME_LOCK_RELEASED"
RUNTIME_LOCK_STALE_CLEARED = "RUNTIME_LOCK_STALE_CLEARED"
RUNTIME_STATE_UPDATED = "RUNTIME_STATE_UPDATED"
RUNTIME_SCHEDULER_STARTED = "RUNTIME_SCHEDULER_STARTED"
RUNTIME_SCHEDULER_STOPPED = "RUNTIME_SCHEDULER_STOPPED"
RUNTIME_TELEGRAM_SUMMARY_SENT = "RUNTIME_TELEGRAM_SUMMARY_SENT"
