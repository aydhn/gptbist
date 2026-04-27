from pathlib import Path
from bist_signal_bot.config.settings import settings
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_DIR = PROJECT_ROOT / settings.DATA_DIR
CACHE_DIR = PROJECT_ROOT / settings.CACHE_DIR
REPORTS_DIR = PROJECT_ROOT / settings.REPORTS_DIR

def ensure_directories_exist():
    """Ensure that necessary application directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
