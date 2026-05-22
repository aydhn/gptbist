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

def get_quality_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import Settings
    s = settings or Settings()
    quality_dir_name = getattr(s, "QUALITY_RESULTS_DIR_NAME", "quality")
    quality_dir = get_data_dir(s) / quality_dir_name
    quality_dir.mkdir(parents=True, exist_ok=True)
    return quality_dir


def get_packaging_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import Settings
    s = settings or Settings()
    return get_data_dir(s) / s.PACKAGING_DIR_NAME


def get_logs_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import Settings
    s = settings or Settings()
    log_dir = Path(s.LOG_DIR)
    if not log_dir.is_absolute():
        log_dir = PROJECT_ROOT / log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def get_reports_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import Settings
    s = settings or Settings()
    rep_dir = Path(s.REPORTS_DIR)
    if not rep_dir.is_absolute():
        rep_dir = PROJECT_ROOT / rep_dir
    rep_dir.mkdir(parents=True, exist_ok=True)
    return rep_dir

def get_docs_dir(settings: Settings | None = None) -> Path:
    from bist_signal_bot.config.settings import get_settings
    s = settings or get_settings()
    return Path(s.DOCS_SOURCE_DIR_NAME)

def get_docs_reports_dir(settings: Settings | None = None) -> Path:
    from bist_signal_bot.config.settings import get_settings
    s = settings or get_settings()
    return get_data_dir(s) / s.DOCS_REPORTS_DIR_NAME

def get_performance_dir(settings: Settings | None = None) -> Path:
    from bist_signal_bot.config.settings import Settings
    s = settings or Settings()
    return get_data_dir(s) / s.PERFORMANCE_DIR_NAME
def get_adaptive_dir(settings: 'Settings | None' = None) -> Path:
    """Returns the path to the adaptive directory."""
    if settings is None:
        from bist_signal_bot.config.settings import get_settings
        settings = get_settings()

    data_dir = get_data_dir(settings)
    adaptive_dir = data_dir / settings.ADAPTIVE_DIR_NAME
    adaptive_dir.mkdir(parents=True, exist_ok=True)
    return adaptive_dir

def get_research_dir(settings: Settings | None = None) -> Path:
    """Gets the base research directory."""
    s = settings or get_settings()
    path = get_data_dir(s) / s.RESEARCH_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_research_ledger_dir(settings: Settings | None = None) -> Path:
    """Gets the research ledger directory."""
    path = get_research_dir(settings) / "ledger"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_research_reports_dir(settings: Settings | None = None) -> Path:
    """Gets the research reports directory."""
    path = get_research_dir(settings) / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_reports_dir(settings: Settings | None = None) -> Path:
    """Gets the path to the reports directory."""
    if settings is None:
        from bist_signal_bot.config.settings import get_settings
        settings = get_settings()

    reports_dir = get_data_dir(settings) / settings.REPORTS_DIR_NAME
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir
import os
from pathlib import Path

def get_scenarios_dir(settings=None) -> Path:
    from bist_signal_bot.storage.paths import get_data_dir
    base = get_data_dir(settings)
    dir_name = getattr(settings, "SCENARIOS_DIR_NAME", "scenarios") if settings else "scenarios"
    p = base / dir_name
    p.mkdir(parents=True, exist_ok=True)
    return p

def get_scenario_runs_dir(settings=None) -> Path:
    p = get_scenarios_dir(settings) / "runs"
    p.mkdir(parents=True, exist_ok=True)
    return p

def get_scenario_golden_dir(settings=None) -> Path:
    p = get_scenarios_dir(settings) / "golden"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_release_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import Settings
    s = settings or Settings()
    release_dir = get_data_dir(s) / getattr(s, "RELEASE_DIR_NAME", "release")
    release_dir.mkdir(parents=True, exist_ok=True)
    return release_dir

def get_imports_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import Settings
    s = settings or Settings()
    path = get_data_dir(s) / getattr(s, "DATA_IMPORTS_DIR_NAME", "imports")
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_lineage_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import Settings
    s = settings or Settings()
    path = get_data_dir(s) / getattr(s, "DATA_LINEAGE_DIR_NAME", "lineage")
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_provider_health_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import Settings
    s = settings or Settings()
    path = get_data_dir(s) / getattr(s, "DATA_PROVIDER_HEALTH_DIR_NAME", "provider_health")
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_ensemble_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import get_settings
    s = settings or get_settings()
    return get_data_dir() / getattr(s, "ENSEMBLE_DIR_NAME", "ensemble")

def get_signals_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import get_settings
    s = settings or get_settings()
    path = get_data_dir(s) / getattr(s, "SIGNALS_DIR_NAME", "signals")
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_portfolio_research_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import Settings
    if settings is None:
        settings = Settings()
    path = get_data_dir(settings) / getattr(settings, "PORTFOLIO_RESEARCH_DIR_NAME", "portfolio_research")
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_stress_dir(settings=None) -> Path:
    base = get_data_dir(settings)
    stress_dir = base / "stress"
    stress_dir.mkdir(parents=True, exist_ok=True)
    return stress_dir

def get_drift_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import Settings
    if settings is None:
        settings = Settings()
    path = get_data_dir(settings) / getattr(settings, "DRIFT_DIR_NAME", "drift")
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_research_lab_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import get_settings
    s = settings or get_settings()
    d = get_data_dir(s) / s.RESEARCH_LAB_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_governance_dir(settings: Settings | None = None) -> Path:
    from bist_signal_bot.config.settings import get_settings
    if settings is None:
        settings = get_settings()

    gov_dir = get_data_dir(settings) / getattr(settings, "GOVERNANCE_DIR_NAME", "governance")
    gov_dir.mkdir(parents=True, exist_ok=True)
    return gov_dir


def get_knowledge_dir(settings: Settings | None = None) -> Path:
    """Gets the directory for the knowledge base storage."""
    base_dir = get_data_dir(settings)
    dir_name = settings.KNOWLEDGE_DIR_NAME if settings else "knowledge"
    knowledge_dir = base_dir / dir_name
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    return knowledge_dir

def get_telegram_center_dir(settings: Settings | None = None) -> Path:
    """Gets the directory for Telegram Center data."""
    base_dir = get_data_dir()
    if settings and hasattr(settings, "TELEGRAM_CENTER_DIR_NAME"):
        dir_name = settings.TELEGRAM_CENTER_DIR_NAME
    else:
        dir_name = "telegram_center"
    path = base_dir / dir_name
    ensure_dir(path)
    return path
