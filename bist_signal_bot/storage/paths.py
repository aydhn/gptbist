from typing import Any
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.config.settings import Settings, settings as default_settings
from bist_signal_bot.data.models import DataVendor, Timeframe
from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol

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

def get_universe_dir(settings: Settings | None = None) -> Path:
    s = settings or default_settings
    data_dir = get_data_dir(s)
    return ensure_dir(data_dir / s.UNIVERSE_DIR_NAME)

def get_universe_file_path(settings: Settings | None = None) -> Path:
    s = settings or default_settings
    universe_dir = get_universe_dir(s)
    return universe_dir / s.UNIVERSE_FILE_NAME

def get_watchlists_dir(settings: Settings | None = None) -> Path:
    s = settings or default_settings
    universe_dir = get_universe_dir(s)
    return ensure_dir(universe_dir / s.WATCHLISTS_DIR_NAME)

def get_universe_snapshots_dir(settings: Settings | None = None) -> Path:
    s = settings or default_settings
    universe_dir = get_universe_dir(s)
    return ensure_dir(universe_dir / s.UNIVERSE_SNAPSHOTS_DIR_NAME)


def get_corporate_actions_dir(settings: Settings | None = None) -> Path:
    s = settings or default_settings
    data_dir = get_data_dir(s)
    return ensure_dir(data_dir / s.CORPORATE_ACTIONS_DIR_NAME)

def get_corporate_actions_file_path(settings: Settings | None = None) -> Path:
    s = settings or default_settings
    ca_dir = get_corporate_actions_dir(s)
    return ca_dir / s.CORPORATE_ACTIONS_FILE_NAME

def get_adjusted_market_data_dir(settings: Settings | None = None) -> Path:
    s = settings or default_settings
    market_data_dir = get_market_data_dir(s)
    return ensure_dir(market_data_dir / "ohlcv_adjusted")

def get_backtest_results_dir(settings: Settings | None = None) -> Path:
    s = settings or default_settings
    reports_dir = PROJECT_ROOT / s.REPORTS_DIR
    return ensure_dir(reports_dir / "backtests")

def get_paper_dir(settings: "Settings | None" = None) -> Path:
    s = settings or _default_settings
    dir_path = get_data_dir(s) / s.PAPER_ACCOUNTS_DIR_NAME
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def get_paper_account_dir(account_id: str, settings: "Settings | None" = None) -> Path:
    dir_path = get_paper_dir(settings) / account_id
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def get_scans_dir(settings: Any | None = None) -> Path:
    from bist_signal_bot.config.settings import Settings
    if settings is None:
        settings = Settings()
    path = Path(settings.DATA_DIR) / settings.SCANNER_RESULTS_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_optimization_dir(settings: "Settings | None" = None) -> Path:
    from bist_signal_bot.config.settings import Settings
    if settings is None:
        settings = Settings()
    path = get_data_dir(settings) / getattr(settings, "OPTIMIZATION_RESULTS_DIR_NAME", "optimization")
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_ml_feature_store_dir(settings=None) -> Path:
    """Gets the path to the ML feature store directory."""
    if settings is None:
        from bist_signal_bot.config.settings import Settings, settings as default_settings
        settings = default_settings

    store_dir = get_data_dir(settings) / getattr(settings, "ML_FEATURE_STORE_DIR_NAME", "ml/features")
    store_dir.mkdir(parents=True, exist_ok=True)
    return store_dir


def get_ml_models_dir(settings: Settings | None = None) -> Path:
    from bist_signal_bot.config.settings import Settings, settings as default_settings
    settings = settings or default_settings
    return get_data_dir() / settings.ML_MODELS_DIR_NAME

def get_ml_training_dir(settings: Settings | None = None) -> Path:
    from bist_signal_bot.config.settings import Settings, settings as default_settings
    settings = settings or default_settings
    return get_data_dir() / settings.ML_TRAINING_DIR_NAME


def get_runtime_dir(settings=None) -> Path:
    base = Path("data") if not settings else Path(settings.DATA_DIR)
    return base / "runtime"

def get_runtime_runs_dir(settings=None) -> Path:
    return get_runtime_dir(settings) / "runs"

def get_monitoring_dir(settings=None) -> Path:
    base = Path("data") if not settings else Path(settings.DATA_DIR)
    dir_name = getattr(settings, "MONITORING_DIR_NAME", "monitoring") if settings else "monitoring"
    path = base / dir_name
    path.mkdir(parents=True, exist_ok=True)
    return path
