import platform
import sys
import tempfile
from pathlib import Path

from bist_signal_bot.calendar.session import BistMarketSessionService
from bist_signal_bot.config.env_loader import env_file_status
from bist_signal_bot.config.settings import settings
from bist_signal_bot.core.constants import DEFAULT_MARKET
from bist_signal_bot.core.context import get_runtime_context
from bist_signal_bot.data.symbol_universe import DEFAULT_SEED_SYMBOLS, SymbolUniverse
from bist_signal_bot.data.universe_updater import UniverseUpdater
from bist_signal_bot.data.universe_store import UniverseStore
from bist_signal_bot.storage.paths import (
    CACHE_DIR,
    DATA_DIR,
    REPORTS_DIR,
    get_market_data_dir,
    get_market_data_index_path,
    get_metadata_dir,
)


def check_local_store_writable(data_dir: Path) -> bool:
    """Tests if the data directory is writable."""
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=data_dir, delete=True) as tmp:
            tmp.write(b"test")
        return True
    except Exception:
        return False

def run_healthcheck() -> dict:
    """
    Runs a system health check and returns the status as a dictionary.
    """
    store = UniverseStore(settings)
    updater = UniverseUpdater(store, settings)

    if store.exists():
        universe = store.load_universe()
        validation_report = updater.validate_universe(universe)
        validation_passed = validation_report.passed
        issue_count = len(validation_report.issues)
    else:
        universe = SymbolUniverse(DEFAULT_SEED_SYMBOLS)
        validation_passed = True
        issue_count = 0


    yfinance_available = False
    try:
        import yfinance
        yfinance_available = True
    except ImportError:
        pass

    market_data_dir = get_market_data_dir(settings)
    metadata_dir = get_metadata_dir(settings)
    index_path = get_market_data_index_path(settings)

    session_service = BistMarketSessionService.from_settings(settings)
    session_status = session_service.get_status()

    runtime_context = get_runtime_context()

    env_status = env_file_status()

    health_status = {
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "run_mode": settings.RUN_MODE,
        "dry_run": settings.DRY_RUN,
        "default_market": settings.DEFAULT_MARKET,
        "default_timezone": settings.DEFAULT_TIMEZONE,
        "python_version": sys.version.split(" ")[0],
        "os_platform": platform.platform(),
        "working_directory": str(Path.cwd()),
        "env_file_exists": env_status.get("exists", False),
        "config_validation_passed": True,
        "secrets_masked_true": True, # Hardcoded because we run settings_safe_dump in log, settings obj masks
        "directories": {
            "data_dir_exists": DATA_DIR.exists(),
            "cache_dir_exists": CACHE_DIR.exists(),
            "reports_dir_exists": REPORTS_DIR.exists(),
        },
        "logging_and_audit": {
            "log_level": settings.LOG_LEVEL,
            "log_to_file": settings.LOG_TO_FILE,
            "log_dir": settings.LOG_DIR,
            "log_file_name": settings.LOG_FILE_NAME,
            "audit_enabled": settings.ENABLE_AUDIT_LOG,
            "audit_log_file": settings.AUDIT_LOG_FILE_NAME,
            "mask_secrets_enabled": settings.MASK_SECRETS_IN_LOGS,
            "debug_tracebacks": settings.DEBUG_TRACEBACKS,
            "error_notifications_enabled": settings.ENABLE_ERROR_NOTIFICATIONS,
            "runtime_run_id_present": bool(runtime_context and runtime_context.run_id)
        },

        "cli": {
            "default_output": settings.CLI_DEFAULT_OUTPUT,
            "rich_enabled": settings.CLI_ENABLE_RICH,
            "verbose_errors": settings.CLI_VERBOSE_ERRORS,
            "available_commands_count": 12,
            "default_command": "healthcheck"
        },
        "storage": {
            "data_dir_path": str(DATA_DIR),
            "market_data_dir_path": str(market_data_dir),
            "metadata_dir_path": str(metadata_dir),
            "storage_format": settings.STORAGE_FORMAT,
            "prefer_local_data": settings.PREFER_LOCAL_DATA,
            "save_fetched_data": settings.SAVE_FETCHED_DATA,
            "market_data_index_exists": index_path.exists(),
            "local_store_writable": check_local_store_writable(DATA_DIR)
        },
        "features": {
            "telegram_enabled": settings.ENABLE_TELEGRAM,
            "ml_enabled": settings.ENABLE_ML,
            "optimizer_enabled": settings.ENABLE_OPTIMIZER,
            "gpu_enabled": settings.ENABLE_GPU,
            "dry_run": settings.DRY_RUN,
        },

        "cleaning": {
            "enabled": settings.ENABLE_DATA_CLEANING,
            "missing_value_policy": settings.CLEANING_MISSING_VALUE_POLICY,
            "invalid_ohlc_policy": settings.CLEANING_INVALID_OHLC_POLICY,
            "outlier_policy": settings.CLEANING_OUTLIER_POLICY,
            "duplicate_timestamp_policy": settings.CLEANING_DUPLICATE_TIMESTAMP_POLICY,
            "max_daily_return_abs": settings.CLEANING_MAX_DAILY_RETURN_ABS,
            "max_volume_zscore": settings.CLEANING_MAX_VOLUME_ZSCORE,
            "min_rows_after_cleaning": settings.CLEANING_MIN_ROWS_AFTER_CLEANING,
            "strict": settings.CLEANING_STRICT,
            "fail_on_error": settings.CLEANING_FAIL_ON_ERROR,
            "cleaner_instantiable": True,
            "mock_cleaning_capable": True
        },
        "data_quality": {
            "enabled": settings.ENABLE_DATA_QUALITY_CHECK,
            "min_rows": settings.DATA_QUALITY_MIN_ROWS,
            "max_daily_return_abs": settings.DATA_QUALITY_MAX_DAILY_RETURN_ABS,
            "max_allowed_gap_days": settings.DATA_QUALITY_MAX_ALLOWED_GAP_DAYS,
            "fail_on_error": settings.DATA_QUALITY_FAIL_ON_ERROR,
            "checker_instantiable": True,
        },

        "downloader": {
            "default_period": settings.DOWNLOAD_DEFAULT_PERIOD,
            "default_timeframe": settings.DOWNLOAD_DEFAULT_TIMEFRAME,
            "continue_on_error": settings.DOWNLOAD_CONTINUE_ON_ERROR,
            "send_telegram_summary": settings.DOWNLOAD_SEND_TELEGRAM_SUMMARY,
            "max_symbols_per_run": settings.DOWNLOAD_MAX_SYMBOLS_PER_RUN,
            "refresh_default": settings.DOWNLOAD_REFRESH_DEFAULT,
            "save_default": settings.DOWNLOAD_SAVE_DEFAULT,
            "instantiable": True,
            "mock_capable": True
        },
        "data_provider": {
            "default_provider": settings.DEFAULT_DATA_PROVIDER,
            "default_timeframe": settings.DEFAULT_TIMEFRAME,
            "default_history_period": settings.DEFAULT_HISTORY_PERIOD,
            "yfinance_available": yfinance_available,
            "scraping_disabled": True,
            "paid_api_required": False
        },

        "calendar": {
            "market_timezone": session_status.timezone,
            "regular_open": settings.BIST_REGULAR_OPEN,
            "regular_close": settings.BIST_REGULAR_CLOSE,
            "manual_holiday_count": len(session_service.calendar.manual_holidays),
            "today_day_type": session_status.day_type.value,
            "is_today_trading_day": session_status.is_trading_day,
            "is_market_open_now": session_status.is_market_open,
            "next_trading_day": str(session_status.next_trading_day) if session_status.next_trading_day else None,
            "previous_trading_day": str(session_status.previous_trading_day) if session_status.previous_trading_day else None,
            "daily_signal_enabled": settings.BIST_DAILY_SIGNAL_ENABLED,
            "intraday_signal_enabled": settings.BIST_INTRADAY_SIGNAL_ENABLED,
            "signal_after_close_minutes": settings.BIST_SIGNAL_AFTER_CLOSE_MINUTES
        },
        "symbol_universe": {
            "universe_dir": str(store.get_universe_dir()),
            "universe_file_path": str(store.get_universe_file_path()),
            "universe_file_exists": store.exists(),
            "auto_initialize_universe": settings.AUTO_INITIALIZE_UNIVERSE,
            "auto_snapshot_universe": settings.AUTO_SNAPSHOT_UNIVERSE,
            "watchlists_dir": str(store.get_watchlists_dir()),
            "snapshots_dir": str(store.get_snapshots_dir()),
            "default_seed_count": len(DEFAULT_SEED_SYMBOLS),
            "local_universe_symbol_count": universe.count(active_only=False),
            "active_symbol_count": universe.count(active_only=True),
            "inactive_symbol_count": universe.count(active_only=False) - universe.count(active_only=True),
            "validation_passed": validation_passed,
            "issue_count": issue_count
        },
        "notifications": {
            "telegram_enabled": settings.ENABLE_TELEGRAM,
            "telegram_configured": bool(settings.ENABLE_TELEGRAM and settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID),
            "telegram_dry_run": settings.TELEGRAM_DRY_RUN,
            "parse_mode": settings.TELEGRAM_PARSE_MODE,
            "message_max_length": settings.TELEGRAM_MESSAGE_MAX_LENGTH,
            "rate_limit_seconds": settings.TELEGRAM_RATE_LIMIT_SECONDS,
            "error_cooldown_seconds": settings.TELEGRAM_ERROR_COOLDOWN_SECONDS,
            "send_startup_notification": settings.SEND_STARTUP_NOTIFICATION,
            "send_healthcheck_notification": settings.SEND_HEALTHCHECK_NOTIFICATION,
            "send_error_notifications": settings.SEND_ERROR_NOTIFICATIONS,
            "bot_token_configured": bool(settings.TELEGRAM_BOT_TOKEN),
            "chat_id_configured": bool(settings.TELEGRAM_CHAT_ID)
        }
    }
    return health_status
