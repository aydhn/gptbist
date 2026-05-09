from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from bist_signal_bot.config import validation
from bist_signal_bot.config.profiles import get_profile
from bist_signal_bot.config.secrets import settings_safe_dump

class Settings(BaseSettings):
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

settings = Settings()
    # Pattern Detection Features
