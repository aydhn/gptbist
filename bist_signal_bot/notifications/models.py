from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class NotificationLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class NotificationType(str, Enum):
    SYSTEM = "SYSTEM"
    HEALTHCHECK = "HEALTHCHECK"
    DATA_PROVIDER = "DATA_PROVIDER"
    DATA_QUALITY = "DATA_QUALITY"
    SIGNAL = "SIGNAL"
    BACKTEST = "BACKTEST"
    PAPER_TRADE = "PAPER_TRADE"
    RISK = "RISK"
    REPORT = "REPORT"
    HEARTBEAT = "HEARTBEAT"
    ERROR = "ERROR"


def get_default_timestamp() -> datetime:
    return datetime.now(timezone.utc)


class NotificationMessage(BaseModel):
    notification_type: NotificationType
    level: NotificationLevel
    title: str = Field(min_length=1)
    body: str
    symbol: str | None = None
    timestamp: datetime = Field(default_factory=get_default_timestamp)
    metadata: dict[str, Any] = Field(default_factory=dict)
    dedup_key: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_symbol(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("symbol"):
                data["symbol"] = str(data["symbol"]).upper().strip()
        return data


class TelegramSendResult(BaseModel):
    success: bool
    message_id: str | int | None = None
    error: str | None = None
    sent_at: datetime | None = None
    dry_run: bool = False
