import sys
import platform
from pathlib import Path
from bist_signal_bot.config.settings import settings
from bist_signal_bot.storage.paths import DATA_DIR, CACHE_DIR, REPORTS_DIR

def run_healthcheck() -> dict:
    """
    Runs a system health check and returns the status as a dictionary.
    """
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
        }
    }
    return health_status
