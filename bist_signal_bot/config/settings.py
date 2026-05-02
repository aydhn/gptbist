from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from bist_signal_bot.config import validation
from bist_signal_bot.config.profiles import get_profile
from bist_signal_bot.config.secrets import settings_safe_dump

class Settings(BaseSettings):
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

        validation.enforce_production_safety(self)

        return self

    def __repr__(self) -> str:
        """Provide a safe string representation hiding secrets."""
        safe_dict = settings_safe_dump(self)
        return f"{self.__class__.__name__}({safe_dict})"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
