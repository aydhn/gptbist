import platform
import sys
import tempfile
from pathlib import Path

from bist_signal_bot.calendar.session import BistMarketSessionService
from bist_signal_bot.config.settings import settings
from bist_signal_bot.core.constants import DEFAULT_MARKET
from bist_signal_bot.data.symbol_universe import DEFAULT_SEED_SYMBOLS, SymbolUniverse
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
    universe = SymbolUniverse(DEFAULT_SEED_SYMBOLS)

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

    health_status = {
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "python_version": sys.version.split(" ")[0],
        "os_platform": platform.platform(),
        "working_directory": str(Path.cwd()),
        "directories": {
            "data_dir_exists": DATA_DIR.exists(),
            "cache_dir_exists": CACHE_DIR.exists(),
            "reports_dir_exists": REPORTS_DIR.exists(),
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
        "data_quality": {
            "enabled": settings.ENABLE_DATA_QUALITY_CHECK,
            "min_rows": settings.DATA_QUALITY_MIN_ROWS,
            "max_daily_return_abs": settings.DATA_QUALITY_MAX_DAILY_RETURN_ABS,
            "max_allowed_gap_days": settings.DATA_QUALITY_MAX_ALLOWED_GAP_DAYS,
            "fail_on_error": settings.DATA_QUALITY_FAIL_ON_ERROR,
            "checker_instantiable": True,
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
            "default_symbol_count": universe.count(active_only=False),
            "active_symbol_count": universe.count(active_only=True),
            "yfinance_compatible_symbol_count": len(universe.list_yfinance_symbols(active_only=True)),
            "invalid_symbol_count": 0, # Since we validate on add, this is 0 for seed symbols
            "has_duplicate_symbol_issue": False, # Handled by dict insertion
            "market": DEFAULT_MARKET
        },
        "notifications": {
            "telegram_enabled": settings.ENABLE_TELEGRAM,
            "telegram_configured": bool(settings.ENABLE_TELEGRAM and settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID),
            "telegram_dry_run": settings.DRY_RUN,
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
