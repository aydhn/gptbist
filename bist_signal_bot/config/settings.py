
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    """
    APP_NAME: str = Field(default="BIST Signal Bot")
    APP_ENV: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")

    DATA_DIR: str = Field(default="data")
    CACHE_DIR: str = Field(default="cache")
    REPORTS_DIR: str = Field(default="reports")

    TELEGRAM_BOT_TOKEN: str = Field(default="")
    TELEGRAM_CHAT_ID: str = Field(default="")

    DEFAULT_TIMEZONE: str = Field(default="Europe/Istanbul")
    DEFAULT_MARKET: str = Field(default="BIST")

    DEFAULT_DATA_PROVIDER: str = Field(default="yfinance")
    DEFAULT_TIMEFRAME: str = Field(default="1d")
    DEFAULT_HISTORY_PERIOD: str = Field(default="2y")
    DATA_PROVIDER_TIMEOUT_SECONDS: int = Field(default=30)
    DATA_PROVIDER_MAX_RETRIES: int = Field(default=2)

    STORAGE_FORMAT: str = Field(default="csv")
    PREFER_LOCAL_DATA: bool = Field(default=True)
    SAVE_FETCHED_DATA: bool = Field(default=True)
    MARKET_DATA_DIR_NAME: str = Field(default="market_data")
    OHLCV_DIR_NAME: str = Field(default="ohlcv")
    METADATA_DIR_NAME: str = Field(default="metadata")
    MARKET_DATA_INDEX_FILE: str = Field(default="market_data_index.json")

    DRY_RUN: bool = Field(default=True)
    ENABLE_TELEGRAM: bool = Field(default=False)
    ENABLE_ML: bool = Field(default=False)
    ENABLE_OPTIMIZER: bool = Field(default=False)
    ENABLE_GPU: bool = Field(default=False)

    ENABLE_DATA_QUALITY_CHECK: bool = Field(default=True)
    DATA_QUALITY_MIN_ROWS: int = Field(default=100)
    DATA_QUALITY_MAX_DAILY_RETURN_ABS: float = Field(default=0.35)
    DATA_QUALITY_MAX_ALLOWED_GAP_DAYS: int = Field(default=10)
    DATA_QUALITY_FAIL_ON_ERROR: bool = Field(default=False)


    MARKET_TIMEZONE: str = Field(default="Europe/Istanbul")
    BIST_REGULAR_OPEN: str = Field(default="10:00")
    BIST_REGULAR_CLOSE: str = Field(default="18:00")
    BIST_SIGNAL_AFTER_CLOSE_MINUTES: int = Field(default=15)
    BIST_INTRADAY_SIGNAL_ENABLED: bool = Field(default=False)
    BIST_DAILY_SIGNAL_ENABLED: bool = Field(default=True)
    BIST_MANUAL_HOLIDAYS: str = Field(default="")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
