from pathlib import Path
from bist_signal_bot.config.settings import Settings, settings as default_settings
from bist_signal_bot.data.models import DataVendor, Timeframe
from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Fallback for old code expecting these constants
DATA_DIR = PROJECT_ROOT / default_settings.DATA_DIR
CACHE_DIR = PROJECT_ROOT / default_settings.CACHE_DIR
REPORTS_DIR = PROJECT_ROOT / default_settings.REPORTS_DIR

def ensure_directories_exist():
    """Ensure that necessary application directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists, creating parents if necessary. Returns the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_data_dir(settings: Settings | None = None) -> Path:
    s = settings or default_settings
    return PROJECT_ROOT / s.DATA_DIR

def get_market_data_dir(settings: Settings | None = None) -> Path:
    s = settings or default_settings
    data_dir = get_data_dir(s)
    return data_dir / s.MARKET_DATA_DIR_NAME

def get_ohlcv_dir(vendor: DataVendor | str, timeframe: Timeframe | str, settings: Settings | None = None) -> Path:
    market_data_dir = get_market_data_dir(settings)
    s = settings or default_settings

    v_str = vendor.value.lower() if isinstance(vendor, DataVendor) else str(vendor).lower()
    tf_str = timeframe.value if isinstance(timeframe, Timeframe) else str(timeframe)

    return market_data_dir / s.OHLCV_DIR_NAME / v_str / tf_str

def get_ohlcv_file_path(symbol: str, vendor: DataVendor | str, timeframe: Timeframe | str, settings: Settings | None = None, extension: str = "csv") -> Path:
    internal_symbol = ensure_valid_internal_symbol(symbol)

    dir_path = get_ohlcv_dir(vendor, timeframe, settings)

    ext = extension
    if ext.startswith("."):
        ext = ext[1:]

    return dir_path / f"{internal_symbol}.{ext}"

def get_metadata_dir(settings: Settings | None = None) -> Path:
    s = settings or default_settings
    market_data_dir = get_market_data_dir(settings)
    return market_data_dir / s.METADATA_DIR_NAME

def get_market_data_index_path(settings: Settings | None = None) -> Path:
    s = settings or default_settings
    meta_dir = get_metadata_dir(settings)
    return meta_dir / s.MARKET_DATA_INDEX_FILE
