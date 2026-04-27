from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

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

    DRY_RUN: bool = Field(default=True)
    ENABLE_TELEGRAM: bool = Field(default=False)
    ENABLE_ML: bool = Field(default=False)
    ENABLE_OPTIMIZER: bool = Field(default=False)
    ENABLE_GPU: bool = Field(default=False)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
