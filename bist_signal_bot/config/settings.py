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

    @model_validator(mode='after')
    def validate_settings(self) -> 'Settings':
        # Apply profile overrides
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

        validation.enforce_production_safety(self)

        return self

    def __repr__(self) -> str:
        """Provide a safe string representation hiding secrets."""
        safe_dict = settings_safe_dump(self)
        return f"{self.__class__.__name__}({safe_dict})"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
