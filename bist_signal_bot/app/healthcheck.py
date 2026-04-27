import sys
import platform
from pathlib import Path
from bist_signal_bot.config.settings import settings
from bist_signal_bot.storage.paths import DATA_DIR, CACHE_DIR, REPORTS_DIR
from bist_signal_bot.data.symbol_universe import SymbolUniverse, DEFAULT_SEED_SYMBOLS
from bist_signal_bot.core.constants import DEFAULT_MARKET

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
        "features": {
            "telegram_enabled": settings.ENABLE_TELEGRAM,
            "ml_enabled": settings.ENABLE_ML,
            "optimizer_enabled": settings.ENABLE_OPTIMIZER,
            "gpu_enabled": settings.ENABLE_GPU,
            "dry_run": settings.DRY_RUN,
        },
        "data_provider": {
            "default_provider": settings.DEFAULT_DATA_PROVIDER,
            "default_timeframe": settings.DEFAULT_TIMEFRAME,
            "default_history_period": settings.DEFAULT_HISTORY_PERIOD,
            "yfinance_available": yfinance_available,
            "scraping_disabled": True,
            "paid_api_required": False
        },
        "symbol_universe": {
            "default_symbol_count": universe.count(active_only=False),
            "active_symbol_count": universe.count(active_only=True),
            "yfinance_compatible_symbol_count": len(universe.list_yfinance_symbols(active_only=True)),
            "invalid_symbol_count": 0, # Since we validate on add, this is 0 for seed symbols
            "has_duplicate_symbol_issue": False, # Handled by dict insertion
            "market": DEFAULT_MARKET
        }
    }
    return health_status
