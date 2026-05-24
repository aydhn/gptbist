from pydantic import Field, model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from bist_signal_bot.config import validation
from bist_signal_bot.config.profiles import get_profile
from bist_signal_bot.config.secrets import settings_safe_dump

class Settings(BaseSettings):

    # --- Instrument Master (Phase 69) ---
    ENABLE_INSTRUMENT_MASTER: bool = True
    INSTRUMENTS_DIR_NAME: str = "instruments"
    INSTRUMENT_MASTER_REQUIRED_FOR_SCANNER: bool = True
    INSTRUMENT_MASTER_ALLOW_UNKNOWN_SYMBOLS: bool = True
    INSTRUMENT_MASTER_IMPORT_REQUIRES_CONFIRM: bool = True
    INSTRUMENT_DEFAULT_CURRENCY: str = "TRY"

    # --- Universe (Phase 69) ---
    UNIVERSE_EXCLUDE_INACTIVE: bool = True
    UNIVERSE_EXCLUDE_DELISTED: bool = True
    UNIVERSE_REQUIRE_RECENT_DATA: bool = False
    UNIVERSE_MIN_AVERAGE_VOLUME: float = 0.0

    # --- Corporate Actions (Phase 69) ---
    ENABLE_CORPORATE_ACTIONS: bool = True
    CORPORATE_ACTIONS_DIR_NAME: str = "corporate_actions"
    CORPORATE_ACTION_IMPORT_REQUIRES_CONFIRM: bool = True
    CORPORATE_ACTION_OVERWRITE_REQUIRES_CONFIRM: bool = True
    CORPORATE_ACTION_VALIDATE_PRICE_GAPS: bool = True
    CORPORATE_ACTION_EXTREME_FACTOR_WARN: float = 0.25

    # --- Adjusted Prices (Phase 69) ---
    ENABLE_ADJUSTED_PRICES: bool = True
    ADJUSTED_PRICES_DIR_NAME: str = "adjusted_prices"
    ADJUSTED_PRICE_DIRECTION: str = "BACKWARD"
    BACKTEST_USE_ADJUSTED_PRICES: bool = True
    SCANNER_USE_ADJUSTED_PRICES: bool = False
    ADJUSTED_CACHE_INVALIDATE_ON_ACTION_IMPORT: bool = True

    # --- Data Quality / Reconciliation (Phase 69) ---
    ENABLE_DATA_RECONCILIATION: bool = True
    DATA_RECONCILIATION_CLOSE_DIFF_WARN_PCT: float = 0.50
    DATA_RECONCILIATION_CLOSE_DIFF_FAIL_PCT: float = 2.00
    DATA_RECONCILIATION_VOLUME_DIFF_WARN_PCT: float = 5.0
    DATA_QUALITY_ABNORMAL_GAP_WARN_PCT: float = 12.0
    DATA_QUALITY_ABNORMAL_GAP_FAIL_PCT: float = 25.0
    REPORT_INCLUDE_MARKET_DATA_MASTER: bool = True


    # --- Config Registry (Phase 68) ---
    ENABLE_CONFIG_REGISTRY: bool = True
    CONFIG_REGISTRY_DIR_NAME: str = 'config_registry'
    CONFIG_REGISTRY_SAVE_SNAPSHOTS: bool = True
    CONFIG_REGISTRY_REDACT_SECRETS: bool = True
    CONFIG_REGISTRY_BLOCK_FORBIDDEN: bool = True
    CONFIG_REGISTRY_WARN_UNKNOWN_ENV: bool = True
    CONFIG_REGISTRY_WARN_DEPRECATED: bool = True
    CONFIG_REGISTRY_DEFAULT_PROFILE: str = 'RESEARCH_ONLY'
    CONFIG_REGISTRY_ALLOW_PROFILE_APPLY: bool = True
    CONFIG_REGISTRY_PROFILE_APPLY_REQUIRES_CONFIRM: bool = True
    CONFIG_REGISTRY_FORCE_RESEARCH_ONLY: bool = True
    CONFIG_REGISTRY_FEATURE_FLAGS_ENABLED: bool = True
    CONFIG_REGISTRY_FLAG_CHANGE_REQUIRES_CONFIRM: bool = True
    CONFIG_REGISTRY_BLOCK_DANGEROUS_FLAGS: bool = True
    CONFIG_REGISTRY_VALIDATE_ON_STARTUP: bool = True
    CONFIG_REGISTRY_VALIDATE_PATHS: bool = True
    CONFIG_REGISTRY_VALIDATE_SECRETS: bool = True
    CONFIG_REGISTRY_VALIDATE_FORBIDDEN_ACTIONS: bool = True
    CONFIG_REGISTRY_SNAPSHOT_ON_FIRST_RUN: bool = True
    CONFIG_REGISTRY_SNAPSHOT_ON_RELEASE: bool = True
    CONFIG_REGISTRY_SNAPSHOT_RETENTION_DAYS: int = 180
    CONFIG_REGISTRY_DRIFT_ENABLED: bool = True
    CONFIG_REGISTRY_DRIFT_WARN_SCORE: float = 30.0
    CONFIG_REGISTRY_DRIFT_FAIL_SCORE: float = 70.0
    RUNTIME_CONFIG_GATE_BEFORE_RUN: bool = False
    RUNTIME_PROFILE: str = 'RESEARCH_ONLY'
    REPORT_INCLUDE_CONFIG_REGISTRY: bool = True
    # Knowledge Base
    ENABLE_KNOWLEDGE_BASE: bool = Field(default=True)
    KNOWLEDGE_DIR_NAME: str = Field(default="knowledge")
    KNOWLEDGE_INDEX_ON_RUNTIME: bool = Field(default=False)
    KNOWLEDGE_RETRIEVE_ON_REVIEW: bool = Field(default=True)
    KNOWLEDGE_RETRIEVE_ON_REPORT: bool = Field(default=True)
    KNOWLEDGE_SAVE_SEARCH_LOGS: bool = Field(default=True)

    # Knowledge Index
    KNOWLEDGE_DEFAULT_SEARCH_MODE: str = Field(default="AUTO")
    KNOWLEDGE_CHUNK_SIZE: int = Field(default=800, gt=0)
    KNOWLEDGE_CHUNK_OVERLAP: int = Field(default=100, ge=0)
    KNOWLEDGE_INCLUDE_ARCHIVED: bool = Field(default=False)
    KNOWLEDGE_INCREMENTAL_INDEX: bool = Field(default=True)
    KNOWLEDGE_REBUILD_REQUIRES_CONFIRM: bool = Field(default=True)

    # Knowledge Sources
    KNOWLEDGE_SOURCE_RESEARCH_LEDGER: bool = Field(default=True)
    KNOWLEDGE_SOURCE_SIGNALS: bool = Field(default=True)
    KNOWLEDGE_SOURCE_REVIEW: bool = Field(default=True)
    KNOWLEDGE_SOURCE_REPORTS: bool = Field(default=True)
    KNOWLEDGE_SOURCE_BACKTESTS: bool = Field(default=True)
    KNOWLEDGE_SOURCE_ENSEMBLE: bool = Field(default=True)
    KNOWLEDGE_SOURCE_PORTFOLIO: bool = Field(default=True)
    KNOWLEDGE_SOURCE_STRESS: bool = Field(default=True)
    KNOWLEDGE_SOURCE_DRIFT: bool = Field(default=True)
    KNOWLEDGE_SOURCE_GOVERNANCE: bool = Field(default=True)
    KNOWLEDGE_SOURCE_MAINTENANCE: bool = Field(default=False)

    # Knowledge Embeddings
    KNOWLEDGE_USE_LOCAL_EMBEDDINGS: bool = Field(default=False)
    KNOWLEDGE_LOCAL_EMBEDDING_MODEL: str = Field(default="")
    KNOWLEDGE_ALLOW_MODEL_DOWNLOAD: bool = Field(default=False)
    KNOWLEDGE_FALLBACK_EMBEDDING_DIM: int = Field(default=128, gt=0)
    KNOWLEDGE_HYBRID_KEYWORD_WEIGHT: float = Field(default=0.60, ge=0.0)
    KNOWLEDGE_HYBRID_EMBEDDING_WEIGHT: float = Field(default=0.40, ge=0.0)

    # Knowledge Search
    KNOWLEDGE_DEFAULT_LIMIT: int = Field(default=10, gt=0)
    KNOWLEDGE_MAX_LIMIT: int = Field(default=50, gt=0)
    KNOWLEDGE_MAX_SNIPPET_CHARS: int = Field(default=300, gt=0)
    KNOWLEDGE_DEDUPE_DOCUMENT_RESULTS: bool = Field(default=True)

    # Knowledge Memory
    KNOWLEDGE_BUILD_MEMORY_CARDS: bool = Field(default=True)
    KNOWLEDGE_MEMORY_MIN_CASES: int = Field(default=3, gt=0)

    @field_validator("KNOWLEDGE_CHUNK_OVERLAP")
    @classmethod
    def validate_overlap(cls, v: int, info: "ValidationInfo") -> int:
        chunk_size = info.data.get("KNOWLEDGE_CHUNK_SIZE", 800)
        if v >= chunk_size:
            raise ValueError("KNOWLEDGE_CHUNK_OVERLAP must be smaller than KNOWLEDGE_CHUNK_SIZE")
        return v

    REPORT_INCLUDE_KNOWLEDGE: bool = Field(default=True)

    # Portfolio Research Settings
    ENABLE_PORTFOLIO_RESEARCH: bool = True
    PORTFOLIO_RESEARCH_DIR_NAME: str = "portfolio_research"
    PORTFOLIO_RESEARCH_MODE: str = "RESEARCH_ONLY"
    PORTFOLIO_RESEARCH_ALLOCATION_METHOD: str = "HYBRID"
    PORTFOLIO_RESEARCH_SAVE_SNAPSHOTS: bool = True
    PORTFOLIO_RESEARCH_INCLUDE_ACTIVE_SIGNALS: bool = True
    PORTFOLIO_RESEARCH_INCLUDE_WATCHLIST: bool = True
    PORTFOLIO_RESEARCH_INCLUDE_ENSEMBLE: bool = True
    PORTFOLIO_RESEARCH_INCLUDE_FUNDAMENTALS: bool = True
    PORTFOLIO_RESEARCH_INCLUDE_BREADTH: bool = True
    PORTFOLIO_RESEARCH_INCLUDE_PAPER_POSITIONS: bool = False
    PORTFOLIO_RESEARCH_MAX_ITEMS: int = 10
    PORTFOLIO_RESEARCH_MAX_SYMBOL_WEIGHT: float = 0.20
    PORTFOLIO_RESEARCH_MAX_SECTOR_WEIGHT: float = 0.35
    PORTFOLIO_RESEARCH_MAX_STRATEGY_WEIGHT: float = 0.40
    PORTFOLIO_RESEARCH_MIN_SCORE: float = 45.0
    PORTFOLIO_RESEARCH_TARGET_GROSS_EXPOSURE: float = 1.00
    PORTFOLIO_RESEARCH_HIGH_CORRELATION_THRESHOLD: float = 0.80
    PORTFOLIO_RESEARCH_MIN_REBALANCE_DELTA: float = 0.025
    PORTFOLIO_RESEARCH_REBALANCE_REQUIRES_CONFIRM: bool = False
    PORTFOLIO_RESEARCH_SIMULATION_INITIAL_VALUE: float = 100000.0
    PORTFOLIO_RESEARCH_SIMULATION_DEFAULT_DAYS: int = 60
    PORTFOLIO_RESEARCH_SIMULATION_INCLUDE_COSTS: bool = True
    PORTFOLIO_RESEARCH_SIMULATION_COST_BPS: float = 20.0
    RUNTIME_BUILD_RESEARCH_PORTFOLIO: bool = False
    RUNTIME_PORTFOLIO_ALLOCATION_METHOD: str | None = "HYBRID"
    RUNTIME_PORTFOLIO_MAX_ITEMS: int | None = 10
    REPORT_INCLUDE_PORTFOLIO_RESEARCH: bool = True

    # Analyst Review
    ENABLE_ANALYST_REVIEW: bool = True
    REVIEW_DIR_NAME: str = "review"
    REVIEW_ADD_SCANNER_SIGNALS: bool = False
    REVIEW_ADD_ENSEMBLE_SIGNALS: bool = True
    REVIEW_ADD_HIGH_PRIORITY_SIGNALS: bool = True
    REVIEW_AUTO_CHECKLIST: bool = True
    REVIEW_REQUIRE_THESIS_FOR_APPROVAL: bool = True
    REVIEW_REQUIRE_CHECKLIST_PASS_FOR_APPROVAL: bool = True
    REVIEW_ALLOW_APPROVE_WITH_WARNINGS: bool = True
    REVIEW_BLOCK_APPROVE_ON_GOVERNANCE_CRITICAL: bool = True

    REVIEW_ITEM_VALIDITY_DAYS: int = 14
    REVIEW_EXPIRE_STALE_ITEMS: bool = True
    REVIEW_STALE_IN_REVIEW_DAYS: int = 7

    REVIEW_FOLLOWUP_ENABLED: bool = True
    REVIEW_DEFAULT_FOLLOWUP_DAYS: int = 3
    REVIEW_REQUIRE_CONFIRM_FOR_FOLLOWUP_CLEAR: bool = True

    REVIEW_REQUIRE_CONFIRM_FOR_DECISION_CHANGE: bool = False
    REVIEW_REQUIRE_CONFIRM_FOR_ARCHIVE: bool = True
    REVIEW_REQUIRE_CONFIRM_FOR_REOPEN: bool = True
    REVIEW_REQUIRE_CONFIRM_FOR_JOURNAL_LESSON: bool = False

    RUNTIME_ADD_SIGNALS_TO_REVIEW: bool = False
    RUNTIME_REVIEW_AUTO_CHECKLIST: bool = True

    SCANNER_ADD_TO_REVIEW: bool = False
    REPORT_INCLUDE_ANALYST_REVIEW: bool = True
    RESEARCH_AUTO_LOG_REVIEW: bool = False


    # --- Breadth / Relative Strength ---
    ENABLE_BREADTH_ENGINE: bool = True
    BREADTH_DIR_NAME: str = "breadth"
    BREADTH_DEFAULT_UNIVERSE: str = "LIQUID"
    BREADTH_DEFAULT_BENCHMARK: str = "XU100"
    BREADTH_DEFAULT_SOURCE: str = "local_file"
    BREADTH_DEFAULT_TIMEFRAME: str = "1d"
    BREADTH_LOOKBACK_DAYS: int = 260
    BREADTH_SAVE_SNAPSHOTS: bool = True
    BREADTH_MA_WINDOWS: str = "20,50,100,200"
    BREADTH_HIGH_LOW_WINDOWS: str = "20,252"
    BREADTH_STRONG_THRESHOLD: float = 75.0
    BREADTH_HEALTHY_THRESHOLD: float = 60.0
    BREADTH_NEUTRAL_THRESHOLD: float = 45.0
    BREADTH_WEAK_THRESHOLD: float = 30.0
    BREADTH_ENABLE_RELATIVE_STRENGTH: bool = True
    BREADTH_RS_WINDOWS: str = "20,50,100,200"
    BREADTH_RS_BENCHMARK_FALLBACK_TO_UNIVERSE: bool = True
    BREADTH_ENABLE_SECTOR_ROTATION: bool = True
    BREADTH_SECTOR_TOP_N: int = 10
    BREADTH_ENABLE_CROSS_SECTIONAL_RANKING: bool = True
    BREADTH_RANK_TOP_N: int = 20
    BREADTH_WEIGHT_RELATIVE_STRENGTH: float = 0.45
    BREADTH_WEIGHT_ABSOLUTE_MOMENTUM: float = 0.20
    BREADTH_WEIGHT_BREADTH_ALIGNMENT: float = 0.15
    BREADTH_WEIGHT_FUNDAMENTAL: float = 0.10
    BREADTH_WEIGHT_LIQUIDITY: float = 0.10
    SCANNER_USE_BREADTH_FILTER: bool = False
    SCANNER_BREADTH_MODE: str = "metadata_only"
    SCANNER_MIN_BREADTH_SCORE: float = 40.0
    SCANNER_MIN_RELATIVE_STRENGTH_SCORE: float = 40.0
    BACKTEST_USE_BREADTH: bool = False
    BACKTEST_BREADTH_LAG_BARS: int = 1
    ML_INCLUDE_BREADTH: bool = False
    RUNTIME_USE_BREADTH: bool = False
    RUNTIME_REFRESH_BREADTH_BEFORE_SCAN: bool = False
    REPORT_INCLUDE_BREADTH: bool = True
    REPORT_INCLUDE_RELATIVE_STRENGTH: bool = True
    REPORT_INCLUDE_SECTOR_ROTATION: bool = True

    ENABLE_FUNDAMENTALS: bool = True
    FUNDAMENTALS_DIR_NAME: str = "fundamentals"
    FUNDAMENTALS_IMPORTS_DIR_NAME: str = "fundamental_imports"
    FUNDAMENTALS_ALLOW_EXCEL: bool = True
    FUNDAMENTALS_ALLOW_PARQUET: bool = True
    FUNDAMENTALS_WEB_IMPORT_ALLOWED: bool = False
    FUNDAMENTALS_DEFAULT_CURRENCY: str = "TRY"
    FUNDAMENTALS_CONSERVATIVE_LAG_DAYS: int = 30
    FUNDAMENTALS_MAX_AGE_DAYS: int = 180
    FUNDAMENTALS_REQUIRE_ANNOUNCED_AT_FOR_BACKTEST: bool = False
    FUNDAMENTALS_ENABLE_FACTOR_SCORING: bool = True
    FUNDAMENTALS_MIN_COMPOSITE_SCORE: float = 40.0
    FUNDAMENTALS_PEER_SCORING_ENABLED: bool = True
    FUNDAMENTALS_EVENT_LOOKBACK_DAYS: int = 30
    FUNDAMENTALS_EVENT_LOOKAHEAD_DAYS: int = 30
    SCANNER_USE_FUNDAMENTAL_FILTER: bool = False
    SCANNER_FUNDAMENTAL_MODE: str = "metadata_only"
    SCANNER_MIN_FUNDAMENTAL_SCORE: float = 40.0
    BACKTEST_USE_FUNDAMENTALS: bool = False
    BACKTEST_FUNDAMENTAL_LAG_DAYS: int = 30
    ML_INCLUDE_FUNDAMENTALS: bool = False
    RUNTIME_USE_FUNDAMENTALS: bool = False
    RUNTIME_REQUIRE_FUNDAMENTAL_FRESHNESS: bool = False
    REPORT_INCLUDE_FUNDAMENTALS: bool = True


    # Docs Settings
    ENABLE_DOCS: bool = True
    DOCS_SOURCE_DIR_NAME: str = "docs"
    DOCS_REPORTS_DIR_NAME: str = "docs"
    DOCS_VALIDATE_ON_QUALITY: bool = True
    DOCS_VALIDATE_UNSAFE_CLAIMS: bool = True
    DOCS_VALIDATE_SECRETS: bool = True
    DOCS_VALIDATE_COMMAND_EXAMPLES: bool = True
    DOCS_RUN_EXAMPLE_SMOKE: bool = False
    DOCS_EXAMPLE_TIMEOUT_SECONDS: int = 30
    DOCS_GENERATE_OVERWRITE: bool = False

    DOCS_INCLUDE_COMMAND_CATALOG: bool = True
    DOCS_COMMAND_EXAMPLES_USE_MOCK: bool = True
    DOCS_WARN_RUNTIME_LOOP_WITHOUT_MAX_ITERATIONS: bool = True

    DOCS_SAVE_VALIDATION_REPORT: bool = True
    DOCS_REPORT_FORMATS: str = "json,markdown,csv"


    # Packaging Settings
    ENABLE_PACKAGING: bool = True
    PACKAGING_DIR_NAME: str = "packaging"
    PACKAGING_MIN_PYTHON_VERSION: str = "3.10"
    PACKAGING_PROJECT_NAME: str = "bist-signal-bot"
    PACKAGING_DEFAULT_FORMAT: str = "MANIFEST_ONLY"
    PACKAGING_RUN_QUALITY_BY_DEFAULT: bool = False
    PACKAGING_RUN_SECURITY_BY_DEFAULT: bool = True
    PACKAGING_INCLUDE_INSTALLERS: bool = True
    PACKAGING_INCLUDE_ENVIRONMENT_REPORT: bool = True
    PACKAGING_INCLUDE_DEPENDENCY_REPORT: bool = True

    # Release Settings
    PACKAGING_RELEASE_VERSION: str = "0.1.0"
    PACKAGING_CREATE_ZIP: bool = False
    PACKAGING_MAX_FILE_SIZE_MB: int = 10
    PACKAGING_EXCLUDE_DATA_DIR: bool = True
    PACKAGING_EXCLUDE_LOGS_DIR: bool = True
    PACKAGING_EXCLUDE_REPORTS_DIR: bool = True
    PACKAGING_EXCLUDE_ENV_FILE: bool = True
    PACKAGING_EXCLUDE_MODEL_ARTIFACTS: bool = True

    # Environment Check Settings
    PACKAGING_WARN_IF_NOT_VENV: bool = True
    PACKAGING_CHECK_WRITE_PERMISSIONS: bool = True
    PACKAGING_CHECK_OPTIONAL_DEPENDENCIES: bool = True
    # Pattern Detection Features
    # DIVERGENCE ENGINE
    ENABLE_DIVERGENCE_ENGINE: bool = Field(default=True)
    DIVERGENCE_FEATURE_LEVEL: str = Field(default="basic")
    DIVERGENCE_PIVOT_MODE: str = Field(default="LOOKBACK_ONLY")
    DIVERGENCE_LOOKBACK: int = Field(default=5)
    DIVERGENCE_CONFIRMATION_BARS: int = Field(default=3)
    DIVERGENCE_MIN_PIVOT_DISTANCE: int = Field(default=3)
    DIVERGENCE_MAX_PIVOT_DISTANCE: int = Field(default=60)
    DIVERGENCE_MIN_STRENGTH_SCORE: float = Field(default=0.0)
    DIVERGENCE_INCLUDE_HIDDEN: bool = Field(default=True)
    DIVERGENCE_INCLUDE_REGULAR: bool = Field(default=True)
    DIVERGENCE_DEFAULT_INDICATORS: str = Field(default="rsi,macd_hist,obv")

    ENABLE_PATTERN_DETECTORS: bool = Field(default=True, description="Enable or disable pattern detectors.")
    PATTERN_FEATURE_LEVEL: str = Field(default="basic", description="Feature level for patterns: basic, advanced, or full.")
    PATTERN_BREAKOUT_WINDOW: int = Field(default=20, description="Window size for breakout detection.")
    PATTERN_SR_WINDOW: int = Field(default=50, description="Window size for support/resistance detection.")
    PATTERN_RANGE_WINDOW: int = Field(default=20, description="Window size for range structure detection.")
    PATTERN_VOLUME_WINDOW: int = Field(default=20, description="Window size for volume-confirmed breakouts.")
    PATTERN_VOLUME_MULTIPLIER: float = Field(default=1.5, description="Volume multiplier for confirmed breakouts.")
    PATTERN_GAP_THRESHOLD: float = Field(default=0.02, description="Percentage threshold for gap detection.")
    PATTERN_SR_TOLERANCE_PCT: float = Field(default=0.02, description="Tolerance percentage for support/resistance.")
    PATTERN_FALSE_BREAKOUT_LAG_BARS: int = Field(default=3, description="Lag bars for false breakout detection.")
    PATTERN_DOJI_BODY_THRESHOLD: float = Field(default=0.1, description="Body to range ratio threshold for Doji.")

    """
    Application settings loaded from environment variables or .env file.
    """
    # APP / RUNTIME
    APP_NAME: str = Field(default="BIST Signal Bot")
    APP_ENV: str = Field(default="development")
    DEFAULT_TIMEZONE: str = Field(default="Europe/Istanbul")
    DEFAULT_MARKET: str = Field(default="BIST")
    DRY_RUN: bool = Field(default=True)
    RUN_MODE: str = Field(default="research")

    # LOGGING
    LOG_LEVEL: str = Field(default="INFO")
    LOG_TO_FILE: bool = Field(default=True)
    LOG_DIR: str = Field(default="logs")
    LOG_FILE_NAME: str = Field(default="bist_signal_bot.log")
    LOG_MAX_BYTES: int = Field(default=5242880)
    LOG_BACKUP_COUNT: int = Field(default=5)
    LOG_FORMAT: str = Field(default="text")
    MASK_SECRETS_IN_LOGS: bool = Field(default=True)
    DEBUG_TRACEBACKS: bool = Field(default=False)


    # CLI
    CLI_DEFAULT_OUTPUT: str = Field(default="text")
    CLI_ENABLE_RICH: bool = Field(default=True)
    CLI_VERBOSE_ERRORS: bool = Field(default=False)

    # AUDIT
    ENABLE_AUDIT_LOG: bool = Field(default=True)
    AUDIT_LOG_FILE_NAME: str = Field(default="audit.log")

    # ERROR HANDLING
    ENABLE_ERROR_NOTIFICATIONS: bool = Field(default=True)
    ERROR_NOTIFICATION_MIN_LEVEL: str = Field(default="ERROR")

    # PATHS
    DATA_DIR: str = Field(default="data")
    CACHE_DIR: str = Field(default="data/cache")
    REPORTS_DIR: str = Field(default="data/reports")

    # DATA PROVIDER
    DEFAULT_DATA_PROVIDER: str = Field(default="yfinance")
    DEFAULT_TIMEFRAME: str = Field(default="1d")
    DEFAULT_HISTORY_PERIOD: str = Field(default="2y")
    DATA_PROVIDER_TIMEOUT_SECONDS: int = Field(default=30)
    DATA_PROVIDER_MAX_RETRIES: int = Field(default=2)
    ENABLE_DATA_PROVIDER_V2: bool = True
    DATA_PROVIDER_DEFAULT_ORDER: str = "local_file,yfinance"
    DATA_PROVIDER_ALLOW_NETWORK: bool = False
    DATA_PROVIDER_PREFER_CACHE: bool = True
    DATA_PROVIDER_RECORD_LINEAGE: bool = True
    DATA_PROVIDER_RECORD_HEALTH: bool = True
    DATA_LOCAL_FILE_ENABLED: bool = True
    DATA_IMPORTS_DIR_NAME: str = "imports"
    DATA_MARKET_DATA_DIR_NAME: str = "market_data"
    DATA_IMPORT_ALLOW_OVERWRITE: bool = False
    DATA_YFINANCE_ENABLED: bool = True
    DATA_YFINANCE_SUFFIX: str = ".IS"
    DATA_YFINANCE_TIMEOUT_SECONDS: int = 30
    DATA_YFINANCE_MAX_RETRIES: int = 1
    DATA_INCREMENTAL_ENABLED: bool = True
    DATA_INCREMENTAL_MAX_AGE_HOURS: float = 48.0
    DATA_INCREMENTAL_LOOKBACK_BARS: int = 5
    DATA_INCREMENTAL_REPAIR_GAPS: bool = True
    DATA_FRESHNESS_MAX_AGE_HOURS: float = 48.0
    DATA_FRESHNESS_WARN_IF_STALE: bool = True
    DATA_COMPARE_CLOSE_TOLERANCE_PCT: float = 0.10
    DATA_COMPARE_VOLUME_TOLERANCE_PCT: float = 5.0
    DATA_SAVE_PARQUET_IF_AVAILABLE: bool = True
    DATA_FALLBACK_TO_CSV: bool = True
    DATA_LINEAGE_DIR_NAME: str = "lineage"
    DATA_PROVIDER_HEALTH_DIR_NAME: str = "provider_health"

    # STORAGE
    STORAGE_FORMAT: str = Field(default="csv")
    PREFER_LOCAL_DATA: bool = Field(default=True)
    SAVE_FETCHED_DATA: bool = Field(default=True)
    MARKET_DATA_DIR_NAME: str = Field(default="market_data")
    OHLCV_DIR_NAME: str = Field(default="ohlcv")
    METADATA_DIR_NAME: str = Field(default="metadata")
    MARKET_DATA_INDEX_FILE: str = Field(default="market_data_index.json")


    # DATA CLEANING
    ENABLE_DATA_CLEANING: bool = Field(default=True)
    CLEANING_MISSING_VALUE_POLICY: str = Field(default="FORWARD_FILL")
    CLEANING_INVALID_OHLC_POLICY: str = Field(default="DROP_ROW")
    CLEANING_OUTLIER_POLICY: str = Field(default="FLAG_ONLY")
    CLEANING_DUPLICATE_TIMESTAMP_POLICY: str = Field(default="KEEP_LAST")
    CLEANING_MAX_DAILY_RETURN_ABS: float = Field(default=0.35)
    CLEANING_MAX_VOLUME_ZSCORE: float = Field(default=8.0)
    CLEANING_MIN_ROWS_AFTER_CLEANING: int = Field(default=100)
    CLEANING_STRICT: bool = Field(default=False)
    CLEANING_FAIL_ON_ERROR: bool = Field(default=True)

    # DATA QUALITY
    ENABLE_DATA_QUALITY_CHECK: bool = Field(default=True)
    DATA_QUALITY_MIN_ROWS: int = Field(default=100)
    DATA_QUALITY_MAX_DAILY_RETURN_ABS: float = Field(default=0.35)
    DATA_QUALITY_MAX_ALLOWED_GAP_DAYS: int = Field(default=10)
    DATA_QUALITY_FAIL_ON_ERROR: bool = Field(default=False)

    # MARKET CALENDAR
    MARKET_TIMEZONE: str = Field(default="Europe/Istanbul")
    BIST_REGULAR_OPEN: str = Field(default="10:00")
    BIST_REGULAR_CLOSE: str = Field(default="18:00")
    BIST_SIGNAL_AFTER_CLOSE_MINUTES: int = Field(default=15)
    BIST_INTRADAY_SIGNAL_ENABLED: bool = Field(default=False)
    BIST_DAILY_SIGNAL_ENABLED: bool = Field(default=True)
    BIST_MANUAL_HOLIDAYS: str = Field(default="")

    # TELEGRAM
    ENABLE_TELEGRAM: bool = Field(default=False)
    TELEGRAM_BOT_TOKEN: str = Field(default="")
    TELEGRAM_CHAT_ID: str = Field(default="")
    TELEGRAM_PARSE_MODE: str = Field(default="HTML")
    TELEGRAM_DISABLE_WEB_PAGE_PREVIEW: bool = Field(default=True)
    TELEGRAM_MESSAGE_MAX_LENGTH: int = Field(default=3900)
    TELEGRAM_SEND_TIMEOUT_SECONDS: int = Field(default=15)
    TELEGRAM_RATE_LIMIT_SECONDS: float = Field(default=1.0)
    TELEGRAM_ERROR_COOLDOWN_SECONDS: float = Field(default=300.0)
    TELEGRAM_DRY_RUN: bool = Field(default=True)
    SEND_STARTUP_NOTIFICATION: bool = Field(default=True)
    SEND_HEALTHCHECK_NOTIFICATION: bool = Field(default=False)
    SEND_ERROR_NOTIFICATIONS: bool = Field(default=True)
    SEND_DATA_QUALITY_WARNINGS: bool = Field(default=True)

    # ML
    ENABLE_ML: bool = Field(default=False)
    ENABLE_GPU: bool = Field(default=False)
    ML_RANDOM_SEED: int = Field(default=42)
    ML_MODEL_DIR: str = Field(default="data/models")

    # OPTIMIZER
    ENABLE_OPTIMIZER: bool = Field(default=False)
    OPTIMIZER_RANDOM_SEED: int = Field(default=42)
    OPTIMIZER_MAX_TRIALS: int = Field(default=100)

    # BACKTEST
    BACKTEST_INITIAL_CAPITAL: float = Field(default=100000.0)
    BACKTEST_COMMISSION_RATE: float = Field(default=0.002)
    BACKTEST_SLIPPAGE_RATE: float = Field(default=0.001)
    BACKTEST_ALLOW_SHORT: bool = Field(default=False)
    # BACKTEST
    ENABLE_BACKTEST_ENGINE: bool = Field(default=True)
    BACKTEST_INITIAL_CAPITAL: float = Field(default=100000.0)
    BACKTEST_EXECUTION_PRICE_MODE: str = Field(default="NEXT_OPEN")
    BACKTEST_COMMISSION_ENABLED: bool = Field(default=True)
    BACKTEST_SLIPPAGE_ENABLED: bool = Field(default=True)
    BACKTEST_ALLOW_SHORT: bool = Field(default=False)
    BACKTEST_MAX_POSITION_SIZE_PCT: float = Field(default=1.0)
    BACKTEST_MIN_TRADE_NOTIONAL: float = Field(default=100.0)
    BACKTEST_CLOSE_ON_OPPOSITE_SIGNAL: bool = Field(default=True)
    BACKTEST_CLOSE_ON_FLAT_SIGNAL: bool = Field(default=False)
    BACKTEST_ONE_POSITION_PER_SYMBOL: bool = Field(default=True)
    BACKTEST_USE_FRACTIONAL_SHARES: bool = Field(default=False)
    BACKTEST_CLOSE_OPEN_POSITIONS_AT_END: bool = Field(default=True)
    BACKTEST_COST_SCENARIO: str = Field(default="BASE")
    BACKTEST_SAVE_RESULTS: bool = Field(default=False)
    BACKTEST_RESULTS_DIR_NAME: str = Field(default="backtests")


    # RISK
    MAX_POSITION_SIZE_PCT: float = Field(default=0.10)
    MAX_PORTFOLIO_RISK_PCT: float = Field(default=0.02)
    MAX_DAILY_SIGNALS: int = Field(default=10)

    # UNIVERSE
    UNIVERSE_DIR_NAME: str = Field(default="universe")
    UNIVERSE_FILE_NAME: str = Field(default="bist_universe.json")
    WATCHLISTS_DIR_NAME: str = Field(default="watchlists")
    UNIVERSE_SNAPSHOTS_DIR_NAME: str = Field(default="snapshots")
    AUTO_INITIALIZE_UNIVERSE: bool = Field(default=True)
    AUTO_SNAPSHOT_UNIVERSE: bool = Field(default=True)
    UNIVERSE_SEND_TELEGRAM_SUMMARY: bool = Field(default=False)
    UNIVERSE_IMPORT_MERGE_DEFAULT: bool = Field(default=True)
    UNIVERSE_IMPORT_DEACTIVATE_MISSING_DEFAULT: bool = Field(default=False)

    # DOWNLOADER
    DOWNLOAD_DEFAULT_PERIOD: str = Field(default="2y")
    DOWNLOAD_DEFAULT_TIMEFRAME: str = Field(default="1d")
    DOWNLOAD_CONTINUE_ON_ERROR: bool = Field(default=True)
    DOWNLOAD_SEND_TELEGRAM_SUMMARY: bool = Field(default=False)
    DOWNLOAD_MAX_SYMBOLS_PER_RUN: int = Field(default=500)
    DOWNLOAD_REFRESH_DEFAULT: bool = Field(default=False)
    DOWNLOAD_SAVE_DEFAULT: bool = Field(default=True)

    # INDICATORS
    # TREND INDICATORS & FEATURES
    ENABLE_TREND_INDICATORS: bool = Field(default=True)
    TREND_FEATURE_LEVEL: str = Field(default="basic")
    TREND_SHORT_WINDOW: int = Field(default=20)
    TREND_MEDIUM_WINDOW: int = Field(default=50)
    TREND_LONG_WINDOW: int = Field(default=200)
    TREND_ADX_WINDOW: int = Field(default=14)
    TREND_ATR_WINDOW: int = Field(default=14)
    TREND_DONCHIAN_WINDOW: int = Field(default=20)
    TREND_KELTNER_EMA_WINDOW: int = Field(default=20)
    TREND_KELTNER_ATR_MULTIPLIER: float = Field(default=2.0)
    TREND_SUPERTREND_ATR_WINDOW: int = Field(default=10)
    TREND_SUPERTREND_MULTIPLIER: float = Field(default=3.0)
    TREND_AROON_WINDOW: int = Field(default=25)
    TREND_LINREG_WINDOW: int = Field(default=20)

    # MOMENTUM FEATURES
    ENABLE_MOMENTUM_INDICATORS: bool = Field(default=True)
    MOMENTUM_FEATURE_LEVEL: str = Field(default="basic")
    MOMENTUM_RSI_WINDOW: int = Field(default=14)
    MOMENTUM_ROC_WINDOW: int = Field(default=10)
    MOMENTUM_STOCH_K_WINDOW: int = Field(default=14)
    MOMENTUM_STOCH_D_WINDOW: int = Field(default=3)
    MOMENTUM_WILLIAMS_WINDOW: int = Field(default=14)
    MOMENTUM_CCI_WINDOW: int = Field(default=20)
    MOMENTUM_MFI_WINDOW: int = Field(default=14)
    MOMENTUM_TSI_SLOW: int = Field(default=25)
    MOMENTUM_TSI_FAST: int = Field(default=13)
    MOMENTUM_TSI_SIGNAL: int = Field(default=7)
    MOMENTUM_PPO_FAST: int = Field(default=12)
    MOMENTUM_PPO_SLOW: int = Field(default=26)
    MOMENTUM_PPO_SIGNAL: int = Field(default=9)
    MOMENTUM_ULTIMATE_SHORT: int = Field(default=7)
    MOMENTUM_ULTIMATE_MEDIUM: int = Field(default=14)
    MOMENTUM_ULTIMATE_LONG: int = Field(default=28)
    MOMENTUM_OVERBOUGHT: float = Field(default=70.0)
    MOMENTUM_OVERSOLD: float = Field(default=30.0)


    ENABLE_INDICATORS: bool = Field(default=True)
    INDICATOR_BACKEND: str = Field(default="native")
    INDICATOR_CONTINUE_ON_ERROR: bool = Field(default=True)
    INDICATOR_DEFAULT_SET: str = Field(default="sma_20,sma_50,ema_20,rsi_14,atr_14,macd,bb_20,obv,return_1,volatility_20")
    INDICATOR_MIN_ROWS_WARNING: int = Field(default=50)
    INDICATOR_SAVE_OUTPUT: bool = Field(default=False)
    # VOLATILITY INDICATORS
    ENABLE_VOLATILITY_INDICATORS: bool = Field(default=True)

    ENABLE_VOLUME_INDICATORS: bool = Field(default=True)
    VOLUME_FEATURE_LEVEL: str = Field(default="basic")
    VOLUME_WINDOW: int = Field(default=20)
    VOLUME_ROC_WINDOW: int = Field(default=10)
    VOLUME_SPIKE_MULTIPLIER: float = Field(default=2.0)
    VOLUME_BREAKOUT_MULTIPLIER: float = Field(default=1.5)
    VOLUME_PRICE_WINDOW: int = Field(default=20)
    VOLUME_CMF_WINDOW: int = Field(default=20)
    VOLUME_FORCE_EMA_SPAN: int = Field(default=13)
    VOLUME_EOM_WINDOW: int = Field(default=14)
    VOLUME_KVO_FAST: int = Field(default=34)
    VOLUME_KVO_SLOW: int = Field(default=55)
    VOLUME_KVO_SIGNAL: int = Field(default=13)
    VOLUME_MIN_TURNOVER_TRY: float = Field(default=1000000.0)
    VOLUME_LIQUIDITY_WINDOW: int = Field(default=20)

    VOLATILITY_FEATURE_LEVEL: str = Field(default="basic")
    VOL_ATR_WINDOW: int = Field(default=14)
    VOL_WINDOW: int = Field(default=20)
    VOL_RANK_WINDOW: int = Field(default=100)
    VOL_REGIME_RANK_WINDOW: int = Field(default=252)
    VOL_BB_WINDOW: int = Field(default=20)
    VOL_BB_STD: float = Field(default=2.0)
    VOL_ANNUALIZATION: int = Field(default=252)
    VOL_Z_WINDOW: int = Field(default=100)
    VOL_GAP_WINDOW: int = Field(default=20)
    VOL_RANGE_WINDOW: int = Field(default=20)


    # CORPORATE ACTIONS & ADJUSTMENTS
    CORPORATE_ACTIONS_DIR_NAME: str = Field(default="corporate_actions")
    CORPORATE_ACTIONS_FILE_NAME: str = Field(default="corporate_actions.json")
    AUTO_INITIALIZE_CORPORATE_ACTIONS: bool = Field(default=True)
    ENABLE_PRICE_ADJUSTMENTS: bool = Field(default=False)
    DEFAULT_ADJUSTMENT_POLICY: str = Field(default="FLAG_ONLY")
    ADJUSTMENT_SAVE_ADJUSTED_DATA: bool = Field(default=False)
    ADJUSTMENT_APPLY_TO_OHLC: bool = Field(default=True)
    ADJUSTMENT_APPLY_TO_VOLUME: bool = Field(default=True)
    ADJUSTMENT_FAIL_ON_ERROR: bool = Field(default=True)
    ADJUSTMENT_REQUIRE_VERIFIED_ACTIONS: bool = Field(default=False)


    # Performance Profiling
    ENABLE_PERFORMANCE_PROFILING: bool = Field(default=True)
    PERFORMANCE_DIR_NAME: str = Field(default="performance")
    PERFORMANCE_SAVE_PROFILES: bool = Field(default=True)
    PERFORMANCE_SAVE_BENCHMARKS: bool = Field(default=True)
    PERFORMANCE_USE_PSUTIL: bool = Field(default=True)
    PERFORMANCE_USE_GPU_SAMPLING: bool = Field(default=True)

    # Profiler
    PERFORMANCE_PROFILE_RUNTIME: bool = Field(default=False)
    PERFORMANCE_PROFILE_SCANNER: bool = Field(default=False)
    PERFORMANCE_RESOURCE_SAMPLE_INTERVAL_SECONDS: float = Field(default=0.5, gt=0.0)
    PERFORMANCE_MAX_RESOURCE_SNAPSHOTS: int = Field(default=500, gt=0)
    PERFORMANCE_SLOW_SPAN_WARN_SECONDS: float = Field(default=2.0, gt=0.0)
    PERFORMANCE_SLOW_SPAN_FAIL_SECONDS: float = Field(default=10.0, gt=0.0)
    PERFORMANCE_MEMORY_DELTA_WARN_MB: float = Field(default=250.0, gt=0.0)
    PERFORMANCE_MEMORY_DELTA_FAIL_MB: float = Field(default=750.0, gt=0.0)

    # Benchmark
    PERFORMANCE_DEFAULT_ITERATIONS: int = Field(default=3, gt=0)
    PERFORMANCE_DEFAULT_WARMUP_ITERATIONS: int = Field(default=1, ge=0)
    PERFORMANCE_DEFAULT_SAMPLE_SIZE: int = Field(default=20, gt=0)
    PERFORMANCE_HEAVY_BENCHMARK_REQUIRES_CONFIRM: bool = Field(default=True)
    PERFORMANCE_SYNTHETIC_DATA_DEFAULT: bool = Field(default=True)
    PERFORMANCE_RANDOM_SEED: int = Field(default=42)

    # Regression
    PERFORMANCE_REGRESSION_ENABLED: bool = Field(default=True)
    PERFORMANCE_ELAPSED_WARN_PCT: float = Field(default=25.0, gt=0.0)
    PERFORMANCE_ELAPSED_FAIL_PCT: float = Field(default=50.0, gt=0.0)
    PERFORMANCE_MEMORY_WARN_PCT: float = Field(default=25.0, gt=0.0)
    PERFORMANCE_MEMORY_FAIL_PCT: float = Field(default=50.0, gt=0.0)

    @model_validator(mode='after')
    def validate_settings(self) -> 'Settings':
        # Apply profile overrides
        if self.TREND_FEATURE_LEVEL not in ["basic", "advanced", "full"]:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("TREND_FEATURE_LEVEL must be basic, advanced, or full")

        if not (0 < self.TREND_SHORT_WINDOW < self.TREND_MEDIUM_WINDOW < self.TREND_LONG_WINDOW):
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("Trend windows must be positive and follow: short < medium < long")

        if any(w <= 0 for w in [self.TREND_ADX_WINDOW, self.TREND_ATR_WINDOW, self.TREND_DONCHIAN_WINDOW,
                               self.TREND_KELTNER_EMA_WINDOW, self.TREND_SUPERTREND_ATR_WINDOW,
                               self.TREND_AROON_WINDOW, self.TREND_LINREG_WINDOW]):
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("Trend window parameters must be positive")

        if self.TREND_KELTNER_ATR_MULTIPLIER <= 0 or self.TREND_SUPERTREND_MULTIPLIER <= 0:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("Trend multiplier parameters must be positive")
        if self.VOLATILITY_FEATURE_LEVEL not in ["basic", "advanced", "full"]:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("VOLATILITY_FEATURE_LEVEL must be basic, advanced, or full")

        if any(w <= 0 for w in [self.VOL_ATR_WINDOW, self.VOL_WINDOW, self.VOL_RANK_WINDOW,
                               self.VOL_REGIME_RANK_WINDOW, self.VOL_BB_WINDOW, self.VOL_ANNUALIZATION,
                               self.VOL_Z_WINDOW, self.VOL_GAP_WINDOW, self.VOL_RANGE_WINDOW]):
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("Volatility window parameters must be positive")

        if self.VOL_BB_STD <= 0:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("Volatility std parameters must be positive")

        if self.VOLUME_FEATURE_LEVEL not in ["basic", "advanced", "full"]:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("VOLUME_FEATURE_LEVEL must be basic, advanced, or full")

        if any(w <= 0 for w in [self.VOLUME_WINDOW, self.VOLUME_ROC_WINDOW, self.VOLUME_PRICE_WINDOW,
                               self.VOLUME_CMF_WINDOW, self.VOLUME_FORCE_EMA_SPAN, self.VOLUME_EOM_WINDOW,
                               self.VOLUME_KVO_FAST, self.VOLUME_KVO_SLOW, self.VOLUME_KVO_SIGNAL,
                               self.VOLUME_LIQUIDITY_WINDOW]):
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("Volume window parameters must be positive integers")

        if self.VOLUME_SPIKE_MULTIPLIER <= 0 or self.VOLUME_BREAKOUT_MULTIPLIER <= 0:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("Volume multiplier parameters must be positive")

        if self.VOLUME_KVO_FAST >= self.VOLUME_KVO_SLOW:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("VOLUME_KVO_FAST must be less than VOLUME_KVO_SLOW")

        if self.VOLUME_MIN_TURNOVER_TRY < 0:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("VOLUME_MIN_TURNOVER_TRY cannot be negative")





        if self.DIVERGENCE_FEATURE_LEVEL not in ["basic", "advanced", "full"]:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("DIVERGENCE_FEATURE_LEVEL must be basic, advanced, or full")

        if self.DIVERGENCE_PIVOT_MODE not in ["LOOKBACK_ONLY", "CONFIRMED_LAGGED"]:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("DIVERGENCE_PIVOT_MODE must be LOOKBACK_ONLY or CONFIRMED_LAGGED")

        if self.DIVERGENCE_LOOKBACK <= 0:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("DIVERGENCE_LOOKBACK must be positive")

        if self.DIVERGENCE_CONFIRMATION_BARS < 0:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("DIVERGENCE_CONFIRMATION_BARS cannot be negative")

        if self.DIVERGENCE_MAX_PIVOT_DISTANCE <= self.DIVERGENCE_MIN_PIVOT_DISTANCE:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("DIVERGENCE_MAX_PIVOT_DISTANCE must be strictly greater than DIVERGENCE_MIN_PIVOT_DISTANCE")

        if not (0.0 <= self.DIVERGENCE_MIN_STRENGTH_SCORE <= 100.0):
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("DIVERGENCE_MIN_STRENGTH_SCORE must be between 0.0 and 100.0")

        if not self.DIVERGENCE_DEFAULT_INDICATORS:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("DIVERGENCE_DEFAULT_INDICATORS cannot be empty")
        if self.PATTERN_FEATURE_LEVEL not in ["basic", "advanced", "full"]:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("PATTERN_FEATURE_LEVEL must be basic, advanced, or full")

        if any(w <= 0 for w in [self.PATTERN_BREAKOUT_WINDOW, self.PATTERN_SR_WINDOW,
                               self.PATTERN_RANGE_WINDOW, self.PATTERN_VOLUME_WINDOW,
                               self.PATTERN_FALSE_BREAKOUT_LAG_BARS]):
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("Pattern window/lag parameters must be positive")

        if self.PATTERN_VOLUME_MULTIPLIER <= 0:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("PATTERN_VOLUME_MULTIPLIER must be positive")

        if self.PATTERN_GAP_THRESHOLD < 0 or self.PATTERN_SR_TOLERANCE_PCT < 0:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("Pattern thresholds and tolerances cannot be negative")

        if not (0 <= self.PATTERN_DOJI_BODY_THRESHOLD <= 1):
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("PATTERN_DOJI_BODY_THRESHOLD must be between 0 and 1")


        if self.PATTERN_FEATURE_LEVEL not in ["basic", "advanced", "full"]:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("PATTERN_FEATURE_LEVEL must be basic, advanced, or full")

        if any(w <= 0 for w in [self.PATTERN_BREAKOUT_WINDOW, self.PATTERN_SR_WINDOW,
                               self.PATTERN_RANGE_WINDOW, self.PATTERN_VOLUME_WINDOW,
                               self.PATTERN_FALSE_BREAKOUT_LAG_BARS]):
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("Pattern window/lag parameters must be positive")

        if self.PATTERN_VOLUME_MULTIPLIER <= 0:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("PATTERN_VOLUME_MULTIPLIER must be positive")

        if self.PATTERN_GAP_THRESHOLD < 0 or self.PATTERN_SR_TOLERANCE_PCT < 0:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("Pattern thresholds and tolerances cannot be negative")

        if not (0 <= self.PATTERN_DOJI_BODY_THRESHOLD <= 1):
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("PATTERN_DOJI_BODY_THRESHOLD must be between 0 and 1")

        profile = get_profile(self.APP_ENV)
        for key, value in profile.safe_defaults.items():
            pass

        # Validations
        self.APP_ENV = validation.validate_app_env(self.APP_ENV)
        self.RUN_MODE = validation.validate_run_mode(self.RUN_MODE)
        self.DEFAULT_MARKET = validation.validate_default_market(self.DEFAULT_MARKET)

        if self.CLI_DEFAULT_OUTPUT not in {"text", "json"}:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError(f"Invalid CLI_DEFAULT_OUTPUT: {self.CLI_DEFAULT_OUTPUT}")

        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.LOG_LEVEL.upper() not in valid_levels:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError(f"Invalid LOG_LEVEL: {self.LOG_LEVEL}. Must be one of {valid_levels}")

        if self.DEFAULT_TIMEFRAME not in {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1wk", "1mo"}:
             from bist_signal_bot.core.exceptions import ConfigurationError
             raise ConfigurationError(f"Unsupported timeframe: {self.DEFAULT_TIMEFRAME}")

        validation.validate_positive_int(self.DATA_PROVIDER_TIMEOUT_SECONDS, "DATA_PROVIDER_TIMEOUT_SECONDS")
        validation.validate_non_negative_int(self.DATA_PROVIDER_MAX_RETRIES, "DATA_PROVIDER_MAX_RETRIES")
        validation.validate_telegram_message_length(self.TELEGRAM_MESSAGE_MAX_LENGTH)
        validation.validate_positive_int(self.TELEGRAM_SEND_TIMEOUT_SECONDS, "TELEGRAM_SEND_TIMEOUT_SECONDS")
        validation.validate_non_negative_float(self.TELEGRAM_RATE_LIMIT_SECONDS, "TELEGRAM_RATE_LIMIT_SECONDS")
        validation.validate_non_negative_float(self.TELEGRAM_ERROR_COOLDOWN_SECONDS, "TELEGRAM_ERROR_COOLDOWN_SECONDS")


        validation.validate_positive_int(self.DATA_QUALITY_MIN_ROWS, "DATA_QUALITY_MIN_ROWS")
        validation.validate_percentage(self.DATA_QUALITY_MAX_DAILY_RETURN_ABS, "DATA_QUALITY_MAX_DAILY_RETURN_ABS")
        validation.validate_positive_int(self.DATA_QUALITY_MAX_ALLOWED_GAP_DAYS, "DATA_QUALITY_MAX_ALLOWED_GAP_DAYS")

        # Cleaning validation
        if self.CLEANING_MISSING_VALUE_POLICY not in ["DROP_ROW", "FORWARD_FILL", "BACKWARD_FILL", "INTERPOLATE", "LEAVE_UNCHANGED", "FAIL"]:
             from bist_signal_bot.core.exceptions import ConfigurationError
             raise ConfigurationError(f"Invalid CLEANING_MISSING_VALUE_POLICY: {self.CLEANING_MISSING_VALUE_POLICY}")

        if self.CLEANING_INVALID_OHLC_POLICY not in ["DROP_ROW", "LEAVE_UNCHANGED", "FAIL"]:
             from bist_signal_bot.core.exceptions import ConfigurationError
             raise ConfigurationError(f"Invalid CLEANING_INVALID_OHLC_POLICY: {self.CLEANING_INVALID_OHLC_POLICY}")

        if self.CLEANING_OUTLIER_POLICY not in ["FLAG_ONLY", "DROP_ROW", "WINSORIZE", "LEAVE_UNCHANGED", "FAIL"]:
             from bist_signal_bot.core.exceptions import ConfigurationError
             raise ConfigurationError(f"Invalid CLEANING_OUTLIER_POLICY: {self.CLEANING_OUTLIER_POLICY}")

        if self.CLEANING_DUPLICATE_TIMESTAMP_POLICY not in ["KEEP_LAST", "KEEP_FIRST", "DROP_ALL", "FAIL"]:
             from bist_signal_bot.core.exceptions import ConfigurationError
             raise ConfigurationError(f"Invalid CLEANING_DUPLICATE_TIMESTAMP_POLICY: {self.CLEANING_DUPLICATE_TIMESTAMP_POLICY}")

        validation.validate_percentage(self.CLEANING_MAX_DAILY_RETURN_ABS, "CLEANING_MAX_DAILY_RETURN_ABS")
        validation.validate_non_negative_float(self.CLEANING_MAX_VOLUME_ZSCORE, "CLEANING_MAX_VOLUME_ZSCORE")
        validation.validate_positive_int(self.CLEANING_MIN_ROWS_AFTER_CLEANING, "CLEANING_MIN_ROWS_AFTER_CLEANING")


        validation.validate_time_format(self.BIST_REGULAR_OPEN, "BIST_REGULAR_OPEN")
        validation.validate_time_format(self.BIST_REGULAR_CLOSE, "BIST_REGULAR_CLOSE")
        validation.validate_market_hours(self.BIST_REGULAR_OPEN, self.BIST_REGULAR_CLOSE)
        validation.validate_iso_date_list(self.BIST_MANUAL_HOLIDAYS)

        validation.validate_storage_format(self.STORAGE_FORMAT)
        validation.validate_positive_int(self.LOG_MAX_BYTES, "LOG_MAX_BYTES")
        validation.validate_non_negative_int(self.LOG_BACKUP_COUNT, "LOG_BACKUP_COUNT")

        validation.validate_positive_int(int(self.BACKTEST_INITIAL_CAPITAL), "BACKTEST_INITIAL_CAPITAL")
        validation.validate_non_negative_float(self.BACKTEST_COMMISSION_RATE, "BACKTEST_COMMISSION_RATE")
        validation.validate_non_negative_float(self.BACKTEST_SLIPPAGE_RATE, "BACKTEST_SLIPPAGE_RATE")

        validation.validate_percentage(self.MAX_POSITION_SIZE_PCT, "MAX_POSITION_SIZE_PCT")
        validation.validate_percentage(self.MAX_PORTFOLIO_RISK_PCT, "MAX_PORTFOLIO_RISK_PCT")
        validation.validate_positive_int(self.MAX_DAILY_SIGNALS, "MAX_DAILY_SIGNALS")

        # Telegram secrets and prod checks
        if self.ENABLE_TELEGRAM and not self.TELEGRAM_DRY_RUN:
            from bist_signal_bot.config.secrets import validate_telegram_secrets
            validate_telegram_secrets(self)

        if not self.UNIVERSE_DIR_NAME:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("UNIVERSE_DIR_NAME cannot be empty")
        if not self.UNIVERSE_FILE_NAME:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("UNIVERSE_FILE_NAME cannot be empty")

        validation.validate_positive_int(self.DOWNLOAD_MAX_SYMBOLS_PER_RUN, "DOWNLOAD_MAX_SYMBOLS_PER_RUN")
        if not self.DOWNLOAD_DEFAULT_PERIOD:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("DOWNLOAD_DEFAULT_PERIOD cannot be empty")
        if self.DOWNLOAD_DEFAULT_TIMEFRAME not in {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1wk", "1mo"}:
             from bist_signal_bot.core.exceptions import ConfigurationError
             raise ConfigurationError(f"Unsupported timeframe: {self.DOWNLOAD_DEFAULT_TIMEFRAME}")


        if self.INDICATOR_BACKEND not in ["native", "ta", "talib", "custom"]:
             from bist_signal_bot.core.exceptions import ConfigurationError
             raise ConfigurationError(f"Invalid INDICATOR_BACKEND: {self.INDICATOR_BACKEND}")
        validation.validate_positive_int(self.INDICATOR_MIN_ROWS_WARNING, "INDICATOR_MIN_ROWS_WARNING")

        if self.DEFAULT_ADJUSTMENT_POLICY not in ["NONE", "USE_PROVIDER_ADJUSTED", "MANUAL_SPLIT_ADJUST", "MANUAL_DIVIDEND_ADJUST", "MANUAL_TOTAL_RETURN", "FLAG_ONLY"]:
             from bist_signal_bot.core.exceptions import ConfigurationError
             raise ConfigurationError(f"Invalid DEFAULT_ADJUSTMENT_POLICY: {self.DEFAULT_ADJUSTMENT_POLICY}")

        if not self.CORPORATE_ACTIONS_DIR_NAME:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("CORPORATE_ACTIONS_DIR_NAME cannot be empty")

        if not self.CORPORATE_ACTIONS_FILE_NAME:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("CORPORATE_ACTIONS_FILE_NAME cannot be empty")


        if getattr(self, "MTF_FEATURE_LEVEL", "basic") not in ["basic", "advanced", "full"]:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("MTF_FEATURE_LEVEL must be basic, advanced, or full")

        if getattr(self, "MTF_BASE_TIMEFRAME", "1d") not in {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1wk", "1mo"}:
             from bist_signal_bot.core.exceptions import ConfigurationError
             raise ConfigurationError(f"Unsupported MTF_BASE_TIMEFRAME: {self.MTF_BASE_TIMEFRAME}")

        if not getattr(self, "MTF_HIGHER_TIMEFRAMES", "1wk"):
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("MTF_HIGHER_TIMEFRAMES cannot be empty")

        if getattr(self, "MTF_ALIGNMENT_MODE", "CLOSED_BAR_ONLY") not in ["CLOSED_BAR_ONLY", "ALLOW_CURRENT_PARTIAL", "EXACT_TIMESTAMP", "ASOF_BACKWARD"]:
             from bist_signal_bot.core.exceptions import ConfigurationError
             raise ConfigurationError(f"Invalid MTF_ALIGNMENT_MODE: {self.MTF_ALIGNMENT_MODE}")

        if not getattr(self, "DEFAULT_BENCHMARKS", ""):
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("DEFAULT_BENCHMARKS cannot be empty")

        if getattr(self, "BENCHMARK_DEFAULT_TIMEFRAME", "1d") not in {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1wk", "1mo"}:
             from bist_signal_bot.core.exceptions import ConfigurationError
             raise ConfigurationError(f"Unsupported BENCHMARK_DEFAULT_TIMEFRAME: {self.BENCHMARK_DEFAULT_TIMEFRAME}")

        validation.validate_percentage(self.BENCHMARK_BUY_AND_HOLD_WEIGHT, "BENCHMARK_BUY_AND_HOLD_WEIGHT")
        validation.validate_positive_int(self.BENCHMARK_MA_WINDOW, "BENCHMARK_MA_WINDOW")
        validation.validate_positive_int(self.BENCHMARK_MOMENTUM_LOOKBACK, "BENCHMARK_MOMENTUM_LOOKBACK")
        validation.validate_positive_int(self.BENCHMARK_VOL_WINDOW, "BENCHMARK_VOL_WINDOW")
        validation.validate_non_negative_float(self.BENCHMARK_MAX_VOL, "BENCHMARK_MAX_VOL")


        if getattr(self, "COST_SCENARIO", "BASE") not in ["OPTIMISTIC", "BASE", "CONSERVATIVE", "STRESS"]:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError(f"Invalid COST_SCENARIO: {self.COST_SCENARIO}")

        if getattr(self, "COMMISSION_MODEL_TYPE", "BPS") not in ["BPS", "FLAT", "BPS_PLUS_FLAT"]:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError(f"Invalid COMMISSION_MODEL_TYPE: {self.COMMISSION_MODEL_TYPE}")

        if getattr(self, "SLIPPAGE_MODEL_TYPE", "HYBRID") not in ["FIXED_BPS", "VOLUME_BASED", "VOLATILITY_BASED", "HYBRID"]:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError(f"Invalid SLIPPAGE_MODEL_TYPE: {self.SLIPPAGE_MODEL_TYPE}")

        if getattr(self, "SPREAD_MODEL_TYPE", "LIQUIDITY_BUCKET") not in ["FIXED_BPS", "LIQUIDITY_BUCKET", "VOLUME_BASED"]:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError(f"Invalid SPREAD_MODEL_TYPE: {self.SPREAD_MODEL_TYPE}")

        validation.validate_non_negative_float(getattr(self, "COMMISSION_BPS", 0.0), "COMMISSION_BPS")
        validation.validate_non_negative_float(getattr(self, "COMMISSION_FLAT_FEE", 0.0), "COMMISSION_FLAT_FEE")
        validation.validate_non_negative_float(getattr(self, "COMMISSION_MINIMUM", 0.0), "COMMISSION_MINIMUM")
        validation.validate_non_negative_float(getattr(self, "TRANSACTION_TAX_BPS", 0.0), "TRANSACTION_TAX_BPS")
        validation.validate_non_negative_float(getattr(self, "OTHER_FEE_BPS", 0.0), "OTHER_FEE_BPS")

        validation.validate_non_negative_float(getattr(self, "FIXED_SLIPPAGE_BPS", 0.0), "FIXED_SLIPPAGE_BPS")
        validation.validate_non_negative_float(getattr(self, "VOLUME_IMPACT_FACTOR", 0.0), "VOLUME_IMPACT_FACTOR")
        validation.validate_non_negative_float(getattr(self, "VOLATILITY_IMPACT_FACTOR", 0.0), "VOLATILITY_IMPACT_FACTOR")
        validation.validate_non_negative_float(getattr(self, "MIN_SLIPPAGE_BPS", 0.0), "MIN_SLIPPAGE_BPS")
        validation.validate_non_negative_float(getattr(self, "MAX_SLIPPAGE_BPS", 0.0), "MAX_SLIPPAGE_BPS")

        min_slip = getattr(self, "MIN_SLIPPAGE_BPS", 0.0)
        max_slip = getattr(self, "MAX_SLIPPAGE_BPS", 0.0)
        if max_slip < min_slip:
            from bist_signal_bot.core.exceptions import ConfigurationError
            raise ConfigurationError("MAX_SLIPPAGE_BPS must be >= MIN_SLIPPAGE_BPS")

        validation.validate_non_negative_float(getattr(self, "FIXED_SPREAD_BPS", 0.0), "FIXED_SPREAD_BPS")
        validation.validate_non_negative_float(getattr(self, "HIGH_LIQUIDITY_SPREAD_BPS", 0.0), "HIGH_LIQUIDITY_SPREAD_BPS")
        validation.validate_non_negative_float(getattr(self, "MEDIUM_LIQUIDITY_SPREAD_BPS", 0.0), "MEDIUM_LIQUIDITY_SPREAD_BPS")
        validation.validate_non_negative_float(getattr(self, "LOW_LIQUIDITY_SPREAD_BPS", 0.0), "LOW_LIQUIDITY_SPREAD_BPS")

        validation.validate_non_negative_float(getattr(self, "COST_DEFAULT_AVG_DAILY_VOLUME", 0.0), "COST_DEFAULT_AVG_DAILY_VOLUME")
        validation.validate_non_negative_float(getattr(self, "COST_DEFAULT_AVG_DAILY_TURNOVER", 0.0), "COST_DEFAULT_AVG_DAILY_TURNOVER")

        high_turnover = getattr(self, "LIQUIDITY_HIGH_TURNOVER_TRY", 100000000.0)
        med_turnover = getattr(self, "LIQUIDITY_MEDIUM_TURNOVER_TRY", 10000000.0)

        if high_turnover <= 0 or med_turnover <= 0:
             from bist_signal_bot.core.exceptions import ConfigurationError
             raise ConfigurationError("LIQUIDITY_*_TURNOVER_TRY must be positive")

        if high_turnover <= med_turnover:
             from bist_signal_bot.core.exceptions import ConfigurationError
             raise ConfigurationError("LIQUIDITY_HIGH_TURNOVER_TRY must be > LIQUIDITY_MEDIUM_TURNOVER_TRY")

        validation.enforce_production_safety(self)


        return self


    def __repr__(self) -> str:
        """Provide a safe string representation hiding secrets."""
        safe_dict = settings_safe_dump(self)
        return f"{self.__class__.__name__}({safe_dict})"



    ENABLE_STRATEGY_ENGINE: bool = Field(default=True)
    DEFAULT_STRATEGY: str = Field(default="moving_average_trend")
    STRATEGY_RUN_MODE: str = Field(default="research")
    STRATEGY_DEFAULT_TIMEFRAME: str = Field(default="1d")
    STRATEGY_ALLOW_SHORT: bool = Field(default=False)
    STRATEGY_CONTINUE_ON_ERROR: bool = Field(default=True)
    STRATEGY_MIN_SCORE: float = Field(default=60.0)
    STRATEGY_USE_LATEST_BAR_ONLY: bool = Field(default=True)
    STRATEGY_SAVE_OUTPUT: bool = Field(default=False)
    STRATEGY_CANDIDATE_DISCLAIMER: str = Field(default="Research signal candidate only. Not investment advice. No order was sent.")

    ENABLE_MULTI_TIMEFRAME: bool = Field(default=True)
    MTF_FEATURE_LEVEL: str = Field(default="basic")
    MTF_BASE_TIMEFRAME: str = Field(default="1d")
    MTF_HIGHER_TIMEFRAMES: str = Field(default="1wk,1mo")
    MTF_ALIGNMENT_MODE: str = Field(default="CLOSED_BAR_ONLY")
    MTF_FORWARD_FILL: bool = Field(default=True)
    MTF_SHIFT_HIGHER_TF_BY_ONE_BAR: bool = Field(default=True)
    MTF_DROP_UNALIGNED_ROWS: bool = Field(default=False)
    MTF_USE_PROVIDER_HIGHER_TF: bool = Field(default=False)
    MTF_RESAMPLE_FROM_BASE: bool = Field(default=True)
    MTF_DROP_INCOMPLETE_HIGHER_TF_BAR: bool = Field(default=True)
    MTF_PREFIX_COLUMNS: bool = Field(default=True)
    MTF_SAVE_OUTPUT: bool = Field(default=False)



    # Benchmark Settings
    ENABLE_BENCHMARKS: bool = Field(default=True)
    DEFAULT_BENCHMARKS: str = Field(default="buy_and_hold,moving_average_benchmark,naive_momentum,naive_volatility_filter")
    BENCHMARK_DEFAULT_TIMEFRAME: str = Field(default="1d")
    BENCHMARK_CONTINUE_ON_ERROR: bool = Field(default=True)
    BENCHMARK_SAVE_OUTPUT: bool = Field(default=False)
    BENCHMARK_BUY_AND_HOLD_WEIGHT: float = Field(default=1.0)
    BENCHMARK_MA_WINDOW: int = Field(default=200)
    BENCHMARK_MOMENTUM_LOOKBACK: int = Field(default=60)
    BENCHMARK_VOL_WINDOW: int = Field(default=20)
    BENCHMARK_MAX_VOL: float = Field(default=0.60)
    BENCHMARK_RANDOM_SEED: int = Field(default=42)


    # COST MODEL
    ENABLE_COST_MODEL: bool = Field(default=True)
    COST_SCENARIO: str = Field(default="BASE")

    COMMISSION_MODEL_TYPE: str = Field(default="BPS")
    COMMISSION_BPS: float = Field(default=5.0)
    COMMISSION_FLAT_FEE: float = Field(default=0.0)
    COMMISSION_MINIMUM: float = Field(default=0.0)
    TRANSACTION_TAX_BPS: float = Field(default=0.0)
    OTHER_FEE_BPS: float = Field(default=0.0)

    SLIPPAGE_MODEL_TYPE: str = Field(default="HYBRID")
    FIXED_SLIPPAGE_BPS: float = Field(default=5.0)
    VOLUME_IMPACT_FACTOR: float = Field(default=10.0)
    VOLATILITY_IMPACT_FACTOR: float = Field(default=0.25)
    MIN_SLIPPAGE_BPS: float = Field(default=0.0)
    MAX_SLIPPAGE_BPS: float = Field(default=100.0)

    SPREAD_MODEL_TYPE: str = Field(default="LIQUIDITY_BUCKET")
    FIXED_SPREAD_BPS: float = Field(default=5.0)
    HIGH_LIQUIDITY_SPREAD_BPS: float = Field(default=3.0)
    MEDIUM_LIQUIDITY_SPREAD_BPS: float = Field(default=8.0)
    LOW_LIQUIDITY_SPREAD_BPS: float = Field(default=20.0)

    LIQUIDITY_HIGH_TURNOVER_TRY: float = Field(default=100000000.0)
    LIQUIDITY_MEDIUM_TURNOVER_TRY: float = Field(default=10000000.0)
    COST_DEFAULT_AVG_DAILY_VOLUME: float = Field(default=0.0)
    COST_DEFAULT_AVG_DAILY_TURNOVER: float = Field(default=0.0)


    # RISK ENGINE
    ENABLE_RISK_ENGINE: bool = Field(default=True)
    RISK_DEFAULT_EQUITY: float = Field(default=100000.0)
    RISK_DEFAULT_AVAILABLE_CASH: float = Field(default=100000.0)
    RISK_ALLOW_SHORT: bool = Field(default=False)
    RISK_USE_FRACTIONAL_SHARES: bool = Field(default=False)

    RISK_POSITION_SIZING_METHOD: str = Field(default="RISK_PERCENT")
    RISK_FIXED_NOTIONAL: float = Field(default=10000.0)
    RISK_EQUITY_POSITION_PCT: float = Field(default=0.10)
    RISK_PER_TRADE_PCT: float = Field(default=0.01)
    RISK_MAX_POSITION_SIZE_PCT: float = Field(default=0.20)
    RISK_MIN_TRADE_NOTIONAL: float = Field(default=100.0)

    RISK_STOP_METHOD: str = Field(default="ATR_MULTIPLE")
    RISK_TARGET_METHOD: str = Field(default="RISK_REWARD_MULTIPLE")
    RISK_FIXED_STOP_PCT: float = Field(default=0.05)
    RISK_FIXED_TARGET_PCT: float = Field(default=0.10)
    RISK_ATR_MULTIPLIER: float = Field(default=2.0)
    RISK_TARGET_R_MULTIPLE: float = Field(default=2.0)
    RISK_SWING_LOOKBACK: int = Field(default=20)

    RISK_MIN_SIGNAL_SCORE: float = Field(default=50.0)
    RISK_MIN_CONFIDENCE: float = Field(default=40.0)
    RISK_MIN_RISK_REWARD: float = Field(default=1.2)
    RISK_MAX_PORTFOLIO_RISK_PCT: float = Field(default=0.05)
    RISK_MAX_DAILY_SIGNALS: int = Field(default=10)
    RISK_MAX_OPEN_POSITIONS: int = Field(default=5)
    RISK_ALLOW_SAME_SYMBOL_POSITION: bool = Field(default=False)
    RISK_MIN_AVG_TURNOVER_TRY: float = Field(default=1000000.0)
    RISK_MAX_VOLATILITY_PCT: float = Field(default=0.80)
    RISK_MAX_ATR_PCT: float = Field(default=0.15)
    RISK_MAX_COST_BPS: float = Field(default=100.0)
    RISK_REJECT_IF_NO_STOP: bool = Field(default=True)
    RISK_REJECT_IF_NO_TARGET: bool = Field(default=False)

    BACKTEST_USE_RISK_ENGINE: bool = Field(default=False)

    # Paper Trading Features
    ENABLE_PAPER_TRADING: bool = Field(default=True)
    PAPER_DEFAULT_ACCOUNT_ID: str = Field(default="default")
    PAPER_INITIAL_CASH: float = Field(default=100000.0)
    PAPER_ACCOUNTS_DIR_NAME: str = Field(default="paper")
    PAPER_REQUIRE_RISK_APPROVAL: bool = Field(default=True)
    PAPER_USE_PORTFOLIO_RISK: bool = Field(default=True)
    PAPER_USE_TRADE_RISK: bool = Field(default=True)
    PAPER_EXECUTION_MODE: str = Field(default="LATEST_CLOSE_RESEARCH")
    PAPER_ALLOW_SHORT: bool = Field(default=False)
    PAPER_USE_FRACTIONAL_SHARES: bool = Field(default=False)

    PAPER_MAX_ORDERS_PER_RUN: int = Field(default=20)
    PAPER_MAX_FILLS_PER_RUN: int = Field(default=20)
    PAPER_REJECT_IF_ACCOUNT_NOT_ACTIVE: bool = Field(default=True)
    PAPER_REJECT_IF_INSUFFICIENT_CASH: bool = Field(default=True)
    PAPER_MARK_TO_MARKET_AFTER_RUN: bool = Field(default=True)
    PAPER_AUTO_EXPORT_CSV: bool = Field(default=False)

    PAPER_FALLBACK_POSITION_NOTIONAL: float = Field(default=10000.0)
    PAPER_FALLBACK_MAX_POSITION_PCT: float = Field(default=0.10)

    PAPER_SEND_TELEGRAM_SUMMARY: bool = Field(default=False)
    PAPER_NOTIFY_ON_FILL: bool = Field(default=False)
    PAPER_NOTIFY_ON_REJECT: bool = Field(default=False)


    # OPTIMIZATION
    ENABLE_OPTIMIZATION: bool = Field(default=True)
    OPTIMIZATION_DEFAULT_METHOD: str = Field(default="GRID_SEARCH")
    OPTIMIZATION_DEFAULT_OBJECTIVE: str = Field(default="COMPOSITE")
    OPTIMIZATION_MAX_COMBINATIONS: int = Field(default=100)
    OPTIMIZATION_RANDOM_SEED: int = Field(default=42)
    OPTIMIZATION_TOP_N: int = Field(default=10)
    OPTIMIZATION_SAVE_REPORT: bool = Field(default=False)
    OPTIMIZATION_REPORT_FORMATS: str = Field(default="json,csv,markdown")
    OPTIMIZATION_RESULTS_DIR_NAME: str = Field(default="optimization")

    # Constraints
    OPTIMIZATION_MIN_TRADES: int = Field(default=3)
    OPTIMIZATION_MAX_DRAWDOWN_PCT: float = Field(default=40.0)
    OPTIMIZATION_MIN_PROFIT_FACTOR: float = Field(default=1.0)
    OPTIMIZATION_MIN_SHARPE: float = Field(default=-10.0)
    OPTIMIZATION_REQUIRE_POSITIVE_RETURN: bool = Field(default=False)
    OPTIMIZATION_REJECT_SAME_CLOSE_RESEARCH: bool = Field(default=True)
    OPTIMIZATION_MAX_COST_PCT_OF_PROFIT: float = Field(default=50.0)

    # Walk-forward
    OPTIMIZATION_WALK_FORWARD_ENABLED: bool = Field(default=False)
    OPTIMIZATION_WF_TRAIN_WINDOW_ROWS: int = Field(default=252)
    OPTIMIZATION_WF_TEST_WINDOW_ROWS: int = Field(default=63)
    OPTIMIZATION_WF_STEP_ROWS: int = Field(default=63)
    OPTIMIZATION_WF_EXPANDING: bool = Field(default=False)
    OPTIMIZATION_WF_MAX_SPLITS: int = Field(default=5)

    # Benchmark
    OPTIMIZATION_COMPARE_BENCHMARK: bool = Field(default=False)
    OPTIMIZATION_BENCHMARK_NAME: str = Field(default="buy_and_hold")

    # Scoring
    OPTIMIZATION_COMPOSITE_RETURN_WEIGHT: float = Field(default=0.25)
    OPTIMIZATION_COMPOSITE_SHARPE_WEIGHT: float = Field(default=0.20)
    OPTIMIZATION_COMPOSITE_SORTINO_WEIGHT: float = Field(default=0.15)
    OPTIMIZATION_COMPOSITE_CALMAR_WEIGHT: float = Field(default=0.15)
    OPTIMIZATION_COMPOSITE_PROFIT_FACTOR_WEIGHT: float = Field(default=0.10)
    OPTIMIZATION_COMPOSITE_DRAWDOWN_WEIGHT: float = Field(default=0.10)
    OPTIMIZATION_COMPOSITE_BENCHMARK_WEIGHT: float = Field(default=0.05)



    # ML TRAINING
    ENABLE_ML_TRAINING: bool = Field(default=True)
    ML_TRAIN_DEFAULT_MODEL_TYPE: str = Field(default="RANDOM_FOREST_CLASSIFIER")
    ML_TRAIN_DEFAULT_TASK_TYPE: str = Field(default="CLASSIFICATION")
    ML_TRAIN_TARGET_COL: str = Field(default="label_direction_binary_5")
    ML_TRAIN_SCALER: str = Field(default="NONE")
    ML_TRAIN_IMPUTER: str = Field(default="MEDIAN")
    ML_TRAIN_RATIO: float = Field(default=0.70)
    ML_TRAIN_RANDOM_SEED: int = Field(default=42)
    ML_TRAIN_MAX_TRAIN_ROWS: int = Field(default=0)
    ML_TRAIN_SAVE_MODEL: bool = Field(default=True)
    ML_TRAIN_SAVE_REPORT: bool = Field(default=False)
    ML_TRAIN_REPORT_FORMATS: str = Field(default="json,markdown,csv")

    ML_RF_N_ESTIMATORS: int = Field(default=100)
    ML_RF_MAX_DEPTH: int | None = Field(default=5)
    ML_RF_MIN_SAMPLES_LEAF: int = Field(default=5)
    ML_GB_N_ESTIMATORS: int = Field(default=100)
    ML_GB_LEARNING_RATE: float = Field(default=0.05)
    ML_GB_MAX_DEPTH: int = Field(default=3)
    ML_LOGISTIC_MAX_ITER: int = Field(default=1000)
    ML_CLASS_WEIGHT: str = Field(default="")

    ML_MODELS_DIR_NAME: str = Field(default="ml/models")
    ML_TRAINING_DIR_NAME: str = Field(default="ml/training")
    ML_PREDICTION_LATEST_ONLY: bool = Field(default=True)
    ML_PREDICTION_MAX_ROWS: int = Field(default=50)

    @field_validator("ML_TRAIN_RATIO")
    @classmethod
    def validate_ml_train_ratio(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("ML_TRAIN_RATIO must be between 0 and 1")
        return v

    @field_validator("ML_TRAIN_MAX_TRAIN_ROWS")
    @classmethod
    def validate_ml_train_max_rows(cls, v: int) -> int:
        if v < 0:
            raise ValueError("ML_TRAIN_MAX_TRAIN_ROWS cannot be negative")
        return v

    @field_validator("ML_RF_N_ESTIMATORS", "ML_GB_N_ESTIMATORS")
    @classmethod
    def validate_n_estimators(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("n_estimators must be positive")
        return v

    @field_validator("ML_RF_MAX_DEPTH")
    @classmethod
    def validate_max_depth(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("max_depth must be positive")
        return v

    @field_validator("ML_GB_LEARNING_RATE")
    @classmethod
    def validate_learning_rate(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("learning_rate must be positive")
        return v


    # ML INFERENCE
    ENABLE_ML_INFERENCE: bool = Field(default=True)
    ML_INFERENCE_DEFAULT_MODEL_ID: str = Field(default="")
    ML_INFERENCE_MODE: str = Field(default="SCORE_AND_FILTER")
    ML_SCORE_BLEND_MODE: str = Field(default="WEIGHTED_AVERAGE")
    ML_SCORE_WEIGHT: float = Field(default=0.35)
    ML_STRATEGY_SCORE_WEIGHT: float = Field(default=0.65)
    ML_MIN_PROBABILITY_POSITIVE: float = Field(default=0.55)
    ML_MAX_PROBABILITY_NEGATIVE: float = Field(default=0.60)
    ML_MIN_PREDICTION_SCORE: float = Field(default=50.0)
    ML_REJECT_ON_MISSING_FEATURES: bool = Field(default=True)
    ML_ALLOW_EXTRA_FEATURES: bool = Field(default=True)
    ML_LATEST_ONLY: bool = Field(default=True)

    STRATEGY_USE_ML_FILTER: bool = Field(default=False)
    STRATEGY_ML_MODEL_ID: str = Field(default="")

    SCANNER_USE_ML_FILTER: bool = Field(default=False)
    SCANNER_ML_MODEL_ID: str = Field(default="")
    SCANNER_MIN_ML_SCORE: float = Field(default=50.0)
    SCANNER_MIN_ML_PROBABILITY: float = Field(default=0.55)

    RISK_USE_ML_FILTER: bool = Field(default=False)
    RISK_MIN_ML_SCORE: float = Field(default=50.0)
    RISK_MIN_ML_PROBABILITY_POSITIVE: float = Field(default=0.55)
    RISK_REJECT_IF_ML_MISSING: bool = Field(default=False)

    BACKTEST_USE_ML_FILTER: bool = Field(default=False)
    BACKTEST_ML_MODEL_ID: str = Field(default="")

    PAPER_USE_ML_FILTER: bool = Field(default=False)
    PAPER_ML_MODEL_ID: str = Field(default="")


    # Market Regime Configuration
    ENABLE_REGIME_ENGINE: bool = Field(default=True)
    REGIME_TREND_WINDOW: int = Field(default=50, gt=0)
    REGIME_VOLATILITY_WINDOW: int = Field(default=20, gt=0)
    REGIME_MOMENTUM_WINDOW: int = Field(default=20, gt=0)
    REGIME_LIQUIDITY_WINDOW: int = Field(default=20, gt=0)
    REGIME_CORRELATION_WINDOW: int = Field(default=60, gt=0)
    REGIME_USE_MTF: bool = Field(default=False)
    REGIME_USE_BENCHMARK_RELATIVE: bool = Field(default=False)
    REGIME_SCORE_MODE: str = Field(default="FILTER_AND_SCORE")
    REGIME_MIN_SCORE: float = Field(default=40.0, ge=0.0, le=100.0)
    REGIME_REJECT_STRESS: bool = Field(default=False)
    REGIME_REDUCE_IN_STRESS: bool = Field(default=True)
    REGIME_STRESS_REDUCTION_FACTOR: float = Field(default=0.50, ge=0.0, le=1.0)
    STRATEGY_USE_REGIME_FILTER: bool = Field(default=False)
    SCANNER_USE_REGIME_FILTER: bool = Field(default=False)
    SCANNER_MIN_REGIME_SCORE: float = Field(default=40.0)
    RISK_USE_REGIME_FILTER: bool = Field(default=False)
    RISK_REJECT_STRESS_REGIME: bool = Field(default=False)
    RISK_REDUCE_IN_STRESS_REGIME: bool = Field(default=True)
    BACKTEST_USE_REGIME_FILTER: bool = Field(default=False)
    PAPER_USE_REGIME_FILTER: bool = Field(default=False)
    ML_INCLUDE_REGIME: bool = Field(default=True)


    # Phase 39 - Runtime Orchestrator
    ENABLE_RUNTIME_ORCHESTRATOR: bool = True
    RUNTIME_MODE: str = "RUN_ONCE"
    RUNTIME_RESULTS_DIR_NAME: str = "runtime"
    RUNTIME_SAVE_REPORTS: bool = True
    RUNTIME_REPORT_FORMATS: str = "json,markdown,csv"
    RUNTIME_CONTINUE_ON_ERROR: bool = True
    RUNTIME_DRY_RUN: bool = False

    RUNTIME_DEFAULT_STRATEGY: str = "moving_average_trend"
    RUNTIME_DEFAULT_SOURCE: str = "mock"
    RUNTIME_DEFAULT_TIMEFRAME: str = "1d"
    RUNTIME_DEFAULT_TOP_N: int = 10
    RUNTIME_UNIVERSE_MODE: str = "GROUP"
    RUNTIME_DEFAULT_GROUP: str = "LIQUID"
    RUNTIME_DEFAULT_WATCHLIST: str = "default"
    RUNTIME_SYMBOLS: str = ""

    RUNTIME_USE_TRADE_RISK: bool = True
    RUNTIME_USE_PORTFOLIO_RISK: bool = True
    RUNTIME_USE_ML_FILTER: bool = False
    RUNTIME_ML_MODEL_ID: str = ""
    RUNTIME_USE_REGIME_FILTER: bool = False

    RUNTIME_USE_PAPER: bool = False
    RUNTIME_REQUIRE_PAPER_CONFIRM_FLAG: bool = True

    RUNTIME_SEND_TELEGRAM: bool = False
    RUNTIME_TELEGRAM_ON_SUCCESS: bool = True
    RUNTIME_TELEGRAM_ON_FAILURE: bool = True
    RUNTIME_TELEGRAM_TOP_N: int = 5

    RUNTIME_SESSION_POLICY: str = "ONLY_DURING_SESSION"
    RUNTIME_SKIP_OUTSIDE_SESSION: bool = True

    RUNTIME_LOCK_TTL_SECONDS: int = 3600
    RUNTIME_CLEAR_STALE_LOCK: bool = True
    RUNTIME_STATE_FILE_NAME: str = "state.json"
    RUNTIME_LOCK_FILE_NAME: str = "runtime.lock"

    RUNTIME_SCHEDULER_ENABLED: bool = False
    RUNTIME_INTERVAL_MINUTES: int = 60
    RUNTIME_RUN_IMMEDIATELY: bool = False
    RUNTIME_MAX_ITERATIONS: int = 0
    RUNTIME_SLEEP_SECONDS: int = 5
    RUNTIME_STOP_ON_FAILURE: bool = False

    RUNTIME_HEALTHCHECK_BEFORE_RUN: bool = True
    RUNTIME_DATA_REFRESH_ENABLED: bool = False
    RUNTIME_CLEANUP_ENABLED: bool = False
    RUNTIME_JOB_MAX_RETRIES: int = 1
    RUNTIME_JOB_RETRY_DELAY_SECONDS: int = 5
    RUNTIME_JOB_TIMEOUT_SECONDS: int = 0

    # Research Reports
    ENABLE_REPORTS: bool = True
    REPORTS_DIR_NAME: str = "reports"
    REPORT_DEFAULT_TYPE: str = "DAILY"
    REPORT_DEFAULT_AUDIENCE: str = "PERSONAL"
    REPORT_DEFAULT_FORMATS: str = "markdown,json,csv"
    REPORT_SAVE_BY_DEFAULT: bool = True
    REPORT_TOP_N: int = 10

    REPORT_INCLUDE_EXECUTIVE_SUMMARY: bool = True
    REPORT_INCLUDE_MARKET_REGIME: bool = True
    REPORT_INCLUDE_SCANNER: bool = True
    REPORT_INCLUDE_RISK: bool = True
    REPORT_INCLUDE_PORTFOLIO_RISK: bool = True
    REPORT_INCLUDE_ML: bool = True
    REPORT_INCLUDE_ADAPTIVE: bool = True
    REPORT_INCLUDE_PAPER: bool = True
    REPORT_INCLUDE_BACKTEST: bool = True
    REPORT_INCLUDE_OPTIMIZATION: bool = True
    REPORT_INCLUDE_RESEARCH_LEDGER: bool = True
    REPORT_INCLUDE_SIGNAL_JOURNAL: bool = True
    REPORT_INCLUDE_ATTRIBUTION: bool = True
    REPORT_INCLUDE_RUNTIME: bool = True
    REPORT_INCLUDE_MONITORING: bool = True
    REPORT_INCLUDE_SECURITY: bool = True
    REPORT_INCLUDE_QUALITY: bool = True
    REPORT_INCLUDE_PERFORMANCE: bool = True

    REPORT_TELEGRAM_DIGEST_ENABLED: bool = False
    REPORT_TELEGRAM_REQUIRE_CONFIRM: bool = True
    REPORT_DIGEST_TOP_N: int = 5
    REPORT_DIGEST_MAX_CHARS: int = 3500

    RUNTIME_GENERATE_REPORT: bool = False
    RUNTIME_REPORT_TYPE: str = "RUNTIME_SUMMARY"
    RUNTIME_SEND_REPORT_DIGEST: bool = False

    REPORT_EXPORT_HTML: bool = True
    REPORT_EXPORT_PDF: bool = False
    REPORT_PDF_REQUIRE_OPTIONAL_DEPENDENCY: bool = True

    RESEARCH_AUTO_LOG_REPORTS: bool = False


    ENABLE_ENSEMBLE_ENGINE: bool = Field(default=True)
    ENSEMBLE_DIR_NAME: str = Field(default="ensemble")
    ENSEMBLE_DEFAULT_MODE: str = Field(default="METADATA_ONLY")
    ENSEMBLE_SAVE_OUTPUTS: bool = Field(default=True)
    ENSEMBLE_DEFAULT_STRATEGIES: str = Field(default="moving_average_trend,breakout_volume,rsi_mean_reversion")

    ENSEMBLE_WEIGHT_STRATEGY: float = Field(default=0.25)
    ENSEMBLE_WEIGHT_INDICATOR: float = Field(default=0.10)
    ENSEMBLE_WEIGHT_PATTERN: float = Field(default=0.05)
    ENSEMBLE_WEIGHT_DIVERGENCE: float = Field(default=0.05)
    ENSEMBLE_WEIGHT_ML: float = Field(default=0.15)
    ENSEMBLE_WEIGHT_REGIME: float = Field(default=0.10)
    ENSEMBLE_WEIGHT_RISK: float = Field(default=0.15)
    ENSEMBLE_WEIGHT_FUNDAMENTAL: float = Field(default=0.05)
    ENSEMBLE_WEIGHT_BREADTH: float = Field(default=0.05)
    ENSEMBLE_WEIGHT_RELATIVE_STRENGTH: float = Field(default=0.03)
    ENSEMBLE_WEIGHT_SECTOR_ROTATION: float = Field(default=0.01)
    ENSEMBLE_WEIGHT_ADAPTIVE: float = Field(default=0.01)

    ENSEMBLE_MIN_APPROVED_SCORE: float = Field(default=70.0)
    ENSEMBLE_MIN_APPROVED_CONFIDENCE: float = Field(default=55.0)
    ENSEMBLE_MIN_AGREEMENT_RATIO: float = Field(default=0.60)
    ENSEMBLE_MAX_CONFLICT_SCORE: float = Field(default=35.0)
    ENSEMBLE_HIGH_CONFLICT_SCORE: float = Field(default=60.0)

    ENSEMBLE_INCLUDE_ML: bool = Field(default=True)
    ENSEMBLE_INCLUDE_REGIME: bool = Field(default=True)
    ENSEMBLE_INCLUDE_RISK: bool = Field(default=True)
    ENSEMBLE_INCLUDE_FUNDAMENTALS: bool = Field(default=True)
    ENSEMBLE_INCLUDE_BREADTH: bool = Field(default=True)
    ENSEMBLE_INCLUDE_ADAPTIVE: bool = Field(default=True)

    SCANNER_USE_ENSEMBLE: bool = Field(default=False)
    SCANNER_ENSEMBLE_MODE: str = Field(default="METADATA_ONLY")
    SCANNER_MIN_CONSENSUS_SCORE: float = Field(default=55.0)
    SCANNER_MIN_CONSENSUS_CONFIDENCE: float = Field(default=45.0)

    BACKTEST_USE_ENSEMBLE: bool = Field(default=False)
    BACKTEST_ENSEMBLE_LAG_BARS: int = Field(default=1)

    RUNTIME_USE_ENSEMBLE: bool = Field(default=False)
    RUNTIME_ENSEMBLE_MODE: str = Field(default="METADATA_ONLY")

    REPORT_INCLUDE_ENSEMBLE: bool = Field(default=True)
    # Governance Settings
    ENABLE_GOVERNANCE: bool = True
    GOVERNANCE_DIR_NAME: str = "governance"
    GOVERNANCE_POLICY_VERSION: str = "1.0.0"
    GOVERNANCE_REQUIRE_RESEARCH_ONLY: bool = True
    GOVERNANCE_BLOCK_REAL_ORDER_LANGUAGE: bool = True
    GOVERNANCE_BLOCK_BROKER_API: bool = True
    GOVERNANCE_BLOCK_PAID_SERVICES: bool = True
    GOVERNANCE_BLOCK_HTML_SCRAPING: bool = True
    GOVERNANCE_REQUIRE_SECRET_REDACTION: bool = True
    GOVERNANCE_REQUIRE_CONFIRM_FOR_POLICY_UPDATE: bool = True

    # Governance Gates
    GOVERNANCE_RUNTIME_GATE_ENABLED: bool = False
    GOVERNANCE_RELEASE_GATE_ENABLED: bool = True
    GOVERNANCE_RESEARCH_LAB_GATE_ENABLED: bool = True
    GOVERNANCE_MAINTENANCE_GATE_ENABLED: bool = True
    GOVERNANCE_REPORT_GATE_ENABLED: bool = False
    GOVERNANCE_ALLOW_WARNINGS: bool = True

    # Governance Evidence Pack
    GOVERNANCE_EVIDENCE_PACK_ENABLED: bool = True
    GOVERNANCE_EVIDENCE_INCLUDE_AUDIT_LOG: bool = True
    GOVERNANCE_EVIDENCE_INCLUDE_RESEARCH_LEDGER: bool = True
    GOVERNANCE_EVIDENCE_INCLUDE_RELEASE_REPORTS: bool = True
    GOVERNANCE_EVIDENCE_INCLUDE_SCENARIO_RESULTS: bool = True
    GOVERNANCE_EVIDENCE_INCLUDE_MAINTENANCE_REPORTS: bool = True
    GOVERNANCE_EVIDENCE_INCLUDE_SETTINGS_SNAPSHOT: bool = True
    GOVERNANCE_EVIDENCE_DRY_RUN_DEFAULT: bool = True

    # Governance Audit
    GOVERNANCE_AUDIT_LOOKBACK_DAYS: int = 30
    GOVERNANCE_BLOCK_ON_CRITICAL_FINDING: bool = True
    GOVERNANCE_WARN_ON_MISSING_DISCLAIMER: bool = True

    # Report Governance Integration
    REPORT_INCLUDE_GOVERNANCE: bool = True


    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")



    # SIGNAL SCANNER
    ENABLE_SIGNAL_SCANNER: bool = Field(default=True)
    SCANNER_DEFAULT_STRATEGY: str = Field(default="moving_average_trend")
    SCANNER_DEFAULT_SOURCE: str = Field(default="mock")
    SCANNER_DEFAULT_TIMEFRAME: str = Field(default="1d")
    SCANNER_DEFAULT_TOP_N: int = Field(default=10)
    SCANNER_CONTINUE_ON_ERROR: bool = Field(default=True)
    SCANNER_SAVE_REPORT: bool = Field(default=False)
    SCANNER_REPORT_FORMATS: str = Field(default="json,csv,markdown")
    SCANNER_SEND_TELEGRAM: bool = Field(default=False)

    SCANNER_USE_TRADE_RISK: bool = Field(default=True)
    SCANNER_USE_PORTFOLIO_RISK: bool = Field(default=True)
    SCANNER_MIN_SIGNAL_SCORE: float = Field(default=50.0)
    SCANNER_MIN_CONFIDENCE: float = Field(default=40.0)
    SCANNER_MIN_FINAL_SCORE: float = Field(default=50.0)
    SCANNER_INCLUDE_WATCH_ONLY: bool = Field(default=True)
    SCANNER_INCLUDE_REJECTED_IN_REPORT: bool = Field(default=True)

    SCANNER_SORT_KEY: str = Field(default="FINAL_SCORE")
    SCANNER_SORT_DESCENDING: bool = Field(default=True)
    SCANNER_LOW_COST_MAX_BPS: float = Field(default=100.0)
    SCANNER_LOW_VOLATILITY_MAX_SCORE: float = Field(default=100.0)

    SCANNER_MAX_SYMBOLS_PER_RUN: int = Field(default=100)
    SCANNER_DEFAULT_WATCHLIST: str = Field(default="default")
    SCANNER_DEFAULT_GROUP: str = Field(default="LIQUID")

    SCANNER_ALLOW_PAPER_EXECUTION: bool = Field(default=False)
    SCANNER_USE_PAPER: bool = Field(default=False)

    SCANNER_RESULTS_DIR_NAME: str = Field(default="scans")


    # Pattern Detection Features

    # SECURITY GUARD
    ENABLE_SECURITY_GUARD: bool = Field(default=True)
    SECURITY_LEVEL: str = Field(default="HIGH")
    SECURITY_FAIL_ON_SECRET_LEAK: bool = Field(default=True)
    SECURITY_REDACT_LOGS: bool = Field(default=True)
    SECURITY_REDACT_AUDIT: bool = Field(default=True)
    SECURITY_REDACT_REPORTS: bool = Field(default=True)
    SECURITY_REDACT_NOTIFICATIONS: bool = Field(default=True)

    SECURITY_BLOCK_REAL_ORDER_ACTIONS: bool = Field(default=True)
    SECURITY_BLOCK_BROKER_API: bool = Field(default=True)
    SECURITY_BLOCK_HTML_SCRAPING: bool = Field(default=True)
    SECURITY_BLOCK_PAID_API: bool = Field(default=True)
    SECURITY_SCAN_SOURCE_FOR_FORBIDDEN_ACTIONS: bool = Field(default=False)

    SECURITY_BLOCK_UNSAFE_CLAIMS: bool = Field(default=True)
    SECURITY_SANITIZE_UNSAFE_CLAIMS: bool = Field(default=True)

    SECURITY_ENFORCE_SAFE_PATHS: bool = Field(default=True)
    SECURITY_ALLOW_EXTERNAL_MODEL_PATH: bool = Field(default=False)

    SECURITY_KILL_SWITCH_ENABLED: bool = Field(default=True)
    SECURITY_KILL_SWITCH_FILE_NAME: str = Field(default="kill_switch.json")
    SECURITY_DEFAULT_KILL_SWITCH_SCOPE: str = Field(default="ALL")

    SECURITY_RUNTIME_PREFLIGHT_ENABLED: bool = Field(default=True)
    SECURITY_NOTIFICATION_PREFLIGHT_ENABLED: bool = Field(default=True)
    SECURITY_REPORT_PREFLIGHT_ENABLED: bool = Field(default=True)
    SECURITY_MODEL_LOAD_PREFLIGHT_ENABLED: bool = Field(default=True)
    SECURITY_CLI_PREFLIGHT_ENABLED: bool = Field(default=True)

    SECURITY_CONFIG_AUDIT_ENABLED: bool = Field(default=True)
    SECURITY_WARN_IF_PAPER_DEFAULT_ACTIVE: bool = Field(default=True)
    SECURITY_WARN_IF_RUNTIME_TELEGRAM_ACTIVE: bool = Field(default=False)
    SECURITY_WARN_IF_SCANNER_PAPER_ENABLED: bool = Field(default=True)
    SECURITY_WARN_IF_SAME_CLOSE_DEFAULT: bool = Field(default=True)


    # Quality Gate Settings
    ENABLE_QUALITY_GATE: bool = True
    QUALITY_RESULTS_DIR_NAME: str = "quality"
    QUALITY_DEFAULT_SUITE: str = "FAST"
    QUALITY_GATE_LEVEL: str = "STANDARD"
    QUALITY_SAVE_REPORT: bool = True
    QUALITY_REPORT_FORMATS: str = "json,markdown,csv"

    QUALITY_RUN_TESTS: bool = True
    QUALITY_RUN_COVERAGE: bool = False
    QUALITY_RUN_STATIC: bool = True
    QUALITY_RUN_TYPE_CHECK: bool = False
    QUALITY_RUN_IMPORT_CHECKS: bool = True
    QUALITY_RUN_SECURITY_CHECKS: bool = True
    QUALITY_RUN_REGRESSION_SMOKE: bool = False
    QUALITY_FAIL_ON_WARNING: bool = False

    QUALITY_COVERAGE_THRESHOLD_PCT: float = 60.0
    QUALITY_TIMEOUT_SECONDS: int = 300
    QUALITY_SMOKE_COMMAND_TIMEOUT_SECONDS: int = 60

    QUALITY_WARN_IF_TOOL_MISSING: bool = True
    QUALITY_STRICT_FAIL_IF_TOOL_MISSING: bool = False

    QUALITY_SMOKE_INCLUDE_BACKTEST: bool = True
    QUALITY_SMOKE_INCLUDE_SCANNER: bool = True
    QUALITY_SMOKE_INCLUDE_ML_DATASET: bool = True
    QUALITY_SMOKE_INCLUDE_RUNTIME_DRY_RUN: bool = True
    QUALITY_SMOKE_INCLUDE_PAPER: bool = False

    RUNTIME_QUALITY_PREFLIGHT_ENABLED: bool = False
    RUNTIME_QUALITY_PREFLIGHT_SUITE: str = 'SMOKE'

    # Performance Settings (Phase 45)


    # Release Manager (Phase 50)
    ENABLE_RELEASE_MANAGER: bool = True
    RELEASE_DIR_NAME: str = "release"
    RELEASE_STAGE: str = "RELEASE_CANDIDATE"
    RELEASE_VERSION: str = "0.1.0"
    RELEASE_PROFILE: str = "FULL_SAFE_LOCAL"
    RELEASE_SAVE_REPORTS: bool = True
    RELEASE_REPORT_FORMATS: str = "json,markdown,csv"

    # Readiness
    RELEASE_RUN_HEALTHCHECK: bool = True
    RELEASE_RUN_SECURITY: bool = True
    RELEASE_RUN_QUALITY: bool = True
    RELEASE_RUN_SCENARIOS: bool = True
    RELEASE_RUN_PACKAGING: bool = True
    RELEASE_RUN_DOCS_VALIDATION: bool = True
    RELEASE_RUN_PERFORMANCE_CHECK: bool = True
    RELEASE_RUN_RUNTIME_DRY_RUN: bool = True
    RELEASE_RUN_REPORT_GENERATION: bool = True

    # Requirements
    RELEASE_REQUIRE_NO_BLOCKERS: bool = True
    RELEASE_REQUIRE_QUALITY_PASS: bool = True
    RELEASE_REQUIRE_SECURITY_PASS: bool = True
    RELEASE_REQUIRE_ACCEPTANCE_PASS: bool = False
    RELEASE_MIN_READY_SCORE: float = 85.0
    RELEASE_MIN_PARTIAL_SCORE: float = 65.0

    # Scenario
    RELEASE_SCENARIO_IDS: str = "smoke,acceptance"
    RELEASE_COMPARE_GOLDEN: bool = False

    # Packaging
    RELEASE_BUILD_PACKAGE: bool = True
    RELEASE_BUILD_ZIP: bool = False
    RELEASE_RUN_SAFE_LAUNCH_REHEARSAL: bool = True

    # Safety
    RELEASE_BLOCK_ON_SECRET_LEAK: bool = True
    RELEASE_BLOCK_ON_FORBIDDEN_ACTION: bool = True
    RELEASE_BLOCK_ON_UNSAFE_CLAIM: bool = True
    RELEASE_BLOCK_ON_BROKER_API: bool = True
    RELEASE_BLOCK_ON_HTML_SCRAPING: bool = True
    RELEASE_BLOCK_ON_REAL_ORDER_LANGUAGE: bool = True

    RESEARCH_AUTO_LOG_RELEASE: bool = False

    def check_release_settings(self) -> 'Settings':
        if not self.RELEASE_VERSION:
            raise ValueError("RELEASE_VERSION cannot be empty")
        if not (0 <= self.RELEASE_MIN_READY_SCORE <= 100):
            raise ValueError("RELEASE_MIN_READY_SCORE must be between 0 and 100")
        if not (0 <= self.RELEASE_MIN_PARTIAL_SCORE <= 100):
            raise ValueError("RELEASE_MIN_PARTIAL_SCORE must be between 0 and 100")
        valid_formats = ["json", "markdown", "csv", "all"]
        for f in self.RELEASE_REPORT_FORMATS.split(","):
            if f.strip().lower() not in valid_formats:
                raise ValueError(f"Invalid format {f} in RELEASE_REPORT_FORMATS")

        # In a real setup, we might also import the Enums and validate stage/profile here,
        # but to avoid circular imports we trust the pydantic/dataclass parsing.
        return self

    def check_performance_settings(self) -> 'Settings':
        if not (0 <= self.PERFORMANCE_MEMORY_WARN_PCT <= 100):
            raise ValueError('Invalid')
        if not (0 <= self.PERFORMANCE_MEMORY_CRITICAL_PCT <= 100):
            raise ValueError('Invalid')
            raise ValueError('Invalid')
            raise ValueError('Invalid')
            raise ValueError('Must be > 0')
            raise ValueError('Must be > 0')
            raise ValueError('Must be > 0')
            raise ValueError('Invalid max batch')
            raise ValueError('Must be > 0')
            raise ValueError('Must be > 0')
            raise ValueError('Invalid')
            raise ValueError('Invalid')
        return self


    RUNTIME_QUALITY_PREFLIGHT_ENABLED: bool = False
    RUNTIME_QUALITY_PREFLIGHT_SUITE: str = "SMOKE"

    # Performance Settings (Phase 45)

    def check_performance_settings(self) -> 'Settings':
        if not (0 <= self.PERFORMANCE_MEMORY_WARN_PCT <= 100):
            raise ValueError("PERFORMANCE_MEMORY_WARN_PCT must be between 0 and 100")
        if not (0 <= self.PERFORMANCE_MEMORY_CRITICAL_PCT <= 100):
            raise ValueError("PERFORMANCE_MEMORY_CRITICAL_PCT must be between 0 and 100")
            raise ValueError("PERFORMANCE_DISK_WARN_PCT must be between 0 and 100")
            raise ValueError("PERFORMANCE_DISK_CRITICAL_PCT must be between 0 and 100")
            raise ValueError("PERFORMANCE_PROFILE_TIMEOUT_SECONDS must be positive")
            raise ValueError("PERFORMANCE_MAX_WORKERS must be positive")
            raise ValueError("PERFORMANCE_DEFAULT_BATCH_SIZE must be positive")
            raise ValueError("PERFORMANCE_MAX_BATCH_SIZE must be >= PERFORMANCE_DEFAULT_BATCH_SIZE")
            raise ValueError("PERFORMANCE_CACHE_MAX_AGE_DAYS must be positive")
            raise ValueError("PERFORMANCE_CACHE_MAX_TOTAL_SIZE_MB must be positive")
            raise ValueError("Invalid PERFORMANCE_CONCURRENCY_MODE")
            raise ValueError("Invalid PERFORMANCE_CACHE_POLICY")
        return self



    # Adaptive Settings (Phase 46)
    ENABLE_ADAPTIVE_ENGINE: bool = True
    ADAPTIVE_MODE: str = "RECOMMEND_ONLY"
    ADAPTIVE_DIR_NAME: str = "adaptive"
    ADAPTIVE_SAVE_REPORTS: bool = True
    ADAPTIVE_REPORT_FORMATS: str = "json,markdown,csv"

    ADAPTIVE_MIN_EVIDENCE_COUNT: int = 2
    ADAPTIVE_MIN_BACKTEST_TRADES: int = 10
    ADAPTIVE_MIN_WALK_FORWARD_SPLITS: int = 3
    ADAPTIVE_MIN_OOS_POSITIVE_SPLIT_PCT: float = 50.0
    ADAPTIVE_MAX_ALLOWED_DRAWDOWN_PCT: float = 35.0
    ADAPTIVE_MIN_PROFIT_FACTOR: float = 1.0
    ADAPTIVE_MIN_SHARPE: float = -5.0
    ADAPTIVE_MIN_PAPER_TRADES: int = 5
    ADAPTIVE_MAX_RECENT_PAPER_DRAWDOWN_PCT: float = 20.0
    ADAPTIVE_MAX_MODEL_AGE_DAYS: int = 30
    ADAPTIVE_MIN_ML_SCORE: float = 50.0
    ADAPTIVE_REQUIRE_REGIME_MATCH: bool = False
    ADAPTIVE_REJECT_HIGH_OVERFIT_WARNING: bool = True
    ADAPTIVE_AUTO_APPLY_REQUIRES_CONFIRM: bool = True

    ADAPTIVE_DEFAULT_TOP_N: int = 5
    ADAPTIVE_DEFAULT_STRATEGIES: str = "moving_average_trend,breakout_volume,rsi_mean_reversion"
    ADAPTIVE_USE_OPTIMIZATION_EVIDENCE: bool = True
    ADAPTIVE_USE_BACKTEST_EVIDENCE: bool = True
    ADAPTIVE_USE_PAPER_EVIDENCE: bool = True
    ADAPTIVE_USE_SCANNER_EVIDENCE: bool = True
    ADAPTIVE_USE_ML_EVIDENCE: bool = True
    ADAPTIVE_USE_REGIME_EVIDENCE: bool = True
    ADAPTIVE_USE_RUNTIME_PERFORMANCE_EVIDENCE: bool = True

    RUNTIME_USE_ADAPTIVE: bool = False
    RUNTIME_ADAPTIVE_MODE: str = "METADATA_ONLY"
    RUNTIME_ADAPTIVE_TOP_N: int = 5

    SCANNER_USE_ADAPTIVE_PARAMS: bool = False


    # Research Settings (Phase 47)
    # Scenario Runner
    ENABLE_SCENARIO_RUNNER: bool = True
    SCENARIOS_DIR_NAME: str = "scenarios"
    SCENARIO_DEFAULT_SYMBOLS: str = "ASELS,THYAO,GARAN"
    SCENARIO_DEFAULT_STRATEGY: str = "moving_average_trend"
    SCENARIO_DEFAULT_SOURCE: str = "mock"
    SCENARIO_DEFAULT_TIMEFRAME: str = "1d"
    SCENARIO_DEFAULT_ROWS: int = 250
    SCENARIO_USE_SANDBOX: bool = True
    SCENARIO_SAVE_OUTPUTS: bool = True
    SCENARIO_COMPARE_GOLDEN: bool = False
    SCENARIO_UPDATE_GOLDEN_REQUIRES_CONFIRM: bool = True

    SCENARIO_DEFAULT_STEP_TIMEOUT_SECONDS: int = 60
    SCENARIO_DEFAULT_TOTAL_TIMEOUT_SECONDS: int = 600
    SCENARIO_SLOW_STEP_SECONDS: float = 15.0

    SCENARIO_DISABLE_TELEGRAM: bool = True
    SCENARIO_FORCE_MOCK_SOURCE: bool = True
    SCENARIO_BLOCK_REAL_ORDER_LANGUAGE: bool = True
    SCENARIO_VALIDATE_OUTPUTS: bool = True
    SCENARIO_CLEANUP_REQUIRES_CONFIRM: bool = True
    ENABLE_RESEARCH_LEDGER: bool = True
    RESEARCH_DIR_NAME: str = "research"
    RESEARCH_LEDGER_APPEND_ONLY: bool = True
    RESEARCH_SAVE_REPORTS: bool = True
    RESEARCH_REPORT_FORMATS: str = "json,markdown,csv"
    RESEARCH_REQUIRE_CONFIRM_FOR_EDITS: bool = True
    RESEARCH_REQUIRE_CONFIRM_FOR_TAG_EDIT: bool = False
    RESEARCH_MAX_RECENT_ENTRIES: int = 100

    RESEARCH_AUTO_LOG_BACKTEST: bool = True
    RESEARCH_AUTO_LOG_OPTIMIZATION: bool = True
    RESEARCH_AUTO_LOG_SCAN: bool = True
    RESEARCH_AUTO_LOG_PAPER: bool = True
    RESEARCH_AUTO_LOG_ML_TRAINING: bool = True
    RESEARCH_AUTO_LOG_ML_INFERENCE: bool = False
    RESEARCH_AUTO_LOG_REGIME: bool = False
    RESEARCH_AUTO_LOG_RUNTIME: bool = True
    RESEARCH_AUTO_LOG_ADAPTIVE: bool = True
    RESEARCH_AUTO_LOG_MONITORING: bool = False

    RESEARCH_SIGNAL_JOURNAL_ENABLED: bool = True
    RESEARCH_JOURNAL_TRACK_OUTCOMES: bool = False
    RESEARCH_JOURNAL_DEFAULT_OUTCOME_HORIZON_BARS: int = 5
    RESEARCH_JOURNAL_REQUIRE_CONFIRM_FOR_OUTCOME_UPDATE: bool = True

    RESEARCH_DEFAULT_COMPARE_METRIC: str = "sharpe"
    RESEARCH_DEFAULT_ATTRIBUTION_GROUP_BY: str = "SYMBOL"

    RESEARCH_REDACT_PAYLOADS: bool = True
    RESEARCH_VALIDATE_NOTES: bool = True
    RESEARCH_VALIDATE_TAGS: bool = True
    RESEARCH_BLOCK_UNSAFE_CLAIMS: bool = True


    # Drift Settings (Phase 58)
    ENABLE_DRIFT_MONITORING: bool = True
    DRIFT_DIR_NAME: str = "drift"
    DRIFT_SAVE_RESULTS: bool = True
    DRIFT_DEFAULT_DOMAINS: str = "FEATURE,MODEL_SCORE,SIGNAL_OUTCOME,STRATEGY_PERFORMANCE,PORTFOLIO_RESEARCH"
    DRIFT_MIN_SAMPLES: int = 30
    DRIFT_REFERENCE_WINDOW_TYPE: str = "LAST_N_DAYS"
    DRIFT_REFERENCE_DAYS: int = 90
    DRIFT_CURRENT_DAYS: int = 14
    DRIFT_REFERENCE_UPDATE_REQUIRES_CONFIRM: bool = True
    DRIFT_FEATURE_PSI_WARN: float = 0.10
    DRIFT_FEATURE_PSI_FAIL: float = 0.25
    DRIFT_FEATURE_PSI_SEVERE: float = 0.50
    DRIFT_FEATURE_KS_WARN: float = 0.20
    DRIFT_FEATURE_KS_FAIL: float = 0.35
    DRIFT_MODEL_SCORE_PSI_WARN: float = 0.10
    DRIFT_MODEL_SCORE_PSI_FAIL: float = 0.25
    DRIFT_MODEL_POSITIVE_RATE_CHANGE_WARN: float = 25.0
    DRIFT_MODEL_POSITIVE_RATE_CHANGE_FAIL: float = 50.0
    DRIFT_CALIBRATION_ENABLED: bool = True
    DRIFT_CALIBRATION_BINS: int = 10
    DRIFT_ECE_WARN: float = 0.08
    DRIFT_ECE_FAIL: float = 0.15
    DRIFT_BRIER_WARN: float = 0.25
    DRIFT_SIGNAL_DECAY_ENABLED: bool = True
    DRIFT_SIGNAL_OUTCOME_DROP_WARN: float = 20.0
    DRIFT_SIGNAL_OUTCOME_DROP_FAIL: float = 40.0
    DRIFT_MUTED_ALERT_RATE_WARN: float = 50.0
    DRIFT_INVALIDATION_RATE_WARN: float = 35.0
    DRIFT_STRATEGY_DECAY_ENABLED: bool = True
    DRIFT_STRATEGY_DECAY_SCORE_WARN: float = 40.0
    DRIFT_STRATEGY_DECAY_SCORE_FAIL: float = 70.0
    DRIFT_PORTFOLIO_DRIFT_ENABLED: bool = True
    DRIFT_EXPOSURE_CHANGE_WARN: float = 0.20
    DRIFT_CONCENTRATION_CHANGE_WARN: float = 0.15
    DRIFT_CORRELATION_CHANGE_WARN: float = 0.20
    RUNTIME_RUN_DRIFT_CHECK: bool = False
    RESEARCH_AUTO_LOG_DRIFT: bool = False


    def check_deployment_settings(self) -> 'Settings':
        if float(self.DEPLOYMENT_MIN_PYTHON_VERSION) < 3.10:
            raise ValueError("DEPLOYMENT_MIN_PYTHON_VERSION must be at least 3.10")
        if self.DEPLOYMENT_DOCTOR_MIN_FREE_DISK_MB <= 0:
            raise ValueError("DEPLOYMENT_DOCTOR_MIN_FREE_DISK_MB must be positive")
        if self.DEPLOYMENT_SMOKE_TIMEOUT_SECONDS <= 0:
            raise ValueError("DEPLOYMENT_SMOKE_TIMEOUT_SECONDS must be positive")
        valid_profiles = ["RESEARCH_ONLY", "PAPER_RESEARCH", "TELEGRAM_DRY_RUN", "LOCAL_SCHEDULER_DRY_RUN", "FULL_LOCAL_SAFE", "DEVELOPMENT", "CUSTOM"]
        if self.DEPLOYMENT_DEFAULT_PROFILE not in valid_profiles:
            raise ValueError(f"Invalid DEPLOYMENT_DEFAULT_PROFILE: {self.DEPLOYMENT_DEFAULT_PROFILE}")
        return self


    # Deployment / First Run Settings
    ENABLE_DEPLOYMENT_TOOLS: bool = True
    DEPLOYMENT_DIR_NAME: str = "deployment"
    DEPLOYMENT_DEFAULT_PROFILE: str = "RESEARCH_ONLY"
    DEPLOYMENT_MIN_PYTHON_VERSION: str = "3.10"
    DEPLOYMENT_REQUIRE_SAFE_PROFILE: bool = True

    FIRST_RUN_DRY_RUN_DEFAULT: bool = True
    FIRST_RUN_CREATE_ENV_TEMPLATE: bool = True
    FIRST_RUN_INIT_DIRECTORIES: bool = True
    FIRST_RUN_RUN_HEALTHCHECK: bool = True
    FIRST_RUN_RUN_GOVERNANCE_GATE: bool = True
    FIRST_RUN_RUN_MAINTENANCE_DOCTOR: bool = True
    FIRST_RUN_CREATE_SCHEDULER_DEFAULTS: bool = False
    FIRST_RUN_RUN_SMOKE_TESTS: bool = True
    FIRST_RUN_GENERATE_RUNBOOK: bool = True
    FIRST_RUN_CONFIRM_WRITE_REQUIRED: bool = True

    DEPLOYMENT_DOCTOR_DEEP_DEFAULT: bool = False
    DEPLOYMENT_DOCTOR_MIN_FREE_DISK_MB: int = 1024
    DEPLOYMENT_DOCTOR_CHECK_IMPORTS: bool = True
    DEPLOYMENT_DOCTOR_CHECK_TIMEZONE: bool = True
    DEPLOYMENT_DOCTOR_CHECK_SECRETS: bool = True
    DEPLOYMENT_DOCTOR_CHECK_PERMISSIONS: bool = True

    DEPLOYMENT_SMOKE_TIMEOUT_SECONDS: int = 30
    DEPLOYMENT_SMOKE_DISABLE_TELEGRAM: bool = True
    DEPLOYMENT_SMOKE_FORCE_RESEARCH_ONLY: bool = True

    DEPLOYMENT_GENERATE_RUNBOOK: bool = True
    DEPLOYMENT_INCLUDE_PLATFORM_COMMANDS: bool = True

    DEPLOYMENT_BLOCK_BROKER_ENABLED: bool = True
    DEPLOYMENT_BLOCK_REAL_ORDER_ENABLED: bool = True
    DEPLOYMENT_BLOCK_PAID_SERVICES: bool = True
    DEPLOYMENT_BLOCK_HTML_SCRAPING: bool = True


    def check_deployment_settings(self) -> 'Settings':
        if float(self.DEPLOYMENT_MIN_PYTHON_VERSION) < 3.10:
            raise ValueError("DEPLOYMENT_MIN_PYTHON_VERSION must be at least 3.10")
        if self.DEPLOYMENT_DOCTOR_MIN_FREE_DISK_MB <= 0:
            raise ValueError("DEPLOYMENT_DOCTOR_MIN_FREE_DISK_MB must be positive")
        if self.DEPLOYMENT_SMOKE_TIMEOUT_SECONDS <= 0:
            raise ValueError("DEPLOYMENT_SMOKE_TIMEOUT_SECONDS must be positive")
        valid_profiles = ["RESEARCH_ONLY", "PAPER_RESEARCH", "TELEGRAM_DRY_RUN", "LOCAL_SCHEDULER_DRY_RUN", "FULL_LOCAL_SAFE", "DEVELOPMENT", "CUSTOM"]
        if self.DEPLOYMENT_DEFAULT_PROFILE not in valid_profiles:
            raise ValueError(f"Invalid DEPLOYMENT_DEFAULT_PROFILE: {self.DEPLOYMENT_DEFAULT_PROFILE}")
        return self


    # Deployment / First Run Settings
    ENABLE_DEPLOYMENT_TOOLS: bool = True
    DEPLOYMENT_DIR_NAME: str = "deployment"
    DEPLOYMENT_DEFAULT_PROFILE: str = "RESEARCH_ONLY"
    DEPLOYMENT_MIN_PYTHON_VERSION: str = "3.10"
    DEPLOYMENT_REQUIRE_SAFE_PROFILE: bool = True

    FIRST_RUN_DRY_RUN_DEFAULT: bool = True
    FIRST_RUN_CREATE_ENV_TEMPLATE: bool = True
    FIRST_RUN_INIT_DIRECTORIES: bool = True
    FIRST_RUN_RUN_HEALTHCHECK: bool = True
    FIRST_RUN_RUN_GOVERNANCE_GATE: bool = True
    FIRST_RUN_RUN_MAINTENANCE_DOCTOR: bool = True
    FIRST_RUN_CREATE_SCHEDULER_DEFAULTS: bool = False
    FIRST_RUN_RUN_SMOKE_TESTS: bool = True
    FIRST_RUN_GENERATE_RUNBOOK: bool = True
    FIRST_RUN_CONFIRM_WRITE_REQUIRED: bool = True

    DEPLOYMENT_DOCTOR_DEEP_DEFAULT: bool = False
    DEPLOYMENT_DOCTOR_MIN_FREE_DISK_MB: int = 1024
    DEPLOYMENT_DOCTOR_CHECK_IMPORTS: bool = True
    DEPLOYMENT_DOCTOR_CHECK_TIMEZONE: bool = True
    DEPLOYMENT_DOCTOR_CHECK_SECRETS: bool = True
    DEPLOYMENT_DOCTOR_CHECK_PERMISSIONS: bool = True

    DEPLOYMENT_SMOKE_TIMEOUT_SECONDS: int = 30
    DEPLOYMENT_SMOKE_DISABLE_TELEGRAM: bool = True
    DEPLOYMENT_SMOKE_FORCE_RESEARCH_ONLY: bool = True

    DEPLOYMENT_GENERATE_RUNBOOK: bool = True
    DEPLOYMENT_INCLUDE_PLATFORM_COMMANDS: bool = True

    DEPLOYMENT_BLOCK_BROKER_ENABLED: bool = True
    DEPLOYMENT_BLOCK_REAL_ORDER_ENABLED: bool = True
    DEPLOYMENT_BLOCK_PAID_SERVICES: bool = True
    DEPLOYMENT_BLOCK_HTML_SCRAPING: bool = True


    def check_deployment_settings(self) -> 'Settings':
        if float(self.DEPLOYMENT_MIN_PYTHON_VERSION) < 3.10:
            raise ValueError("DEPLOYMENT_MIN_PYTHON_VERSION must be at least 3.10")
        if self.DEPLOYMENT_DOCTOR_MIN_FREE_DISK_MB <= 0:
            raise ValueError("DEPLOYMENT_DOCTOR_MIN_FREE_DISK_MB must be positive")
        if self.DEPLOYMENT_SMOKE_TIMEOUT_SECONDS <= 0:
            raise ValueError("DEPLOYMENT_SMOKE_TIMEOUT_SECONDS must be positive")
        valid_profiles = ["RESEARCH_ONLY", "PAPER_RESEARCH", "TELEGRAM_DRY_RUN", "LOCAL_SCHEDULER_DRY_RUN", "FULL_LOCAL_SAFE", "DEVELOPMENT", "CUSTOM"]
        if self.DEPLOYMENT_DEFAULT_PROFILE not in valid_profiles:
            raise ValueError(f"Invalid DEPLOYMENT_DEFAULT_PROFILE: {self.DEPLOYMENT_DEFAULT_PROFILE}")
        return self

    def check_drift_settings(self) -> 'Settings':
        return self



def get_settings() -> Settings:
    global _settings_instance
    if '_settings_instance' not in globals():
        _settings_instance = Settings()
    return _settings_instance

settings = get_settings()
