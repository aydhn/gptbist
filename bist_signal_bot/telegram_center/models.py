from enum import Enum
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

class TelegramCommandStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PARSED = "PARSED"
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"

class TelegramCommandDecision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK_FORBIDDEN_ACTION = "BLOCK_FORBIDDEN_ACTION"
    BLOCK_UNAUTHORIZED = "BLOCK_UNAUTHORIZED"
    BLOCK_UNKNOWN_COMMAND = "BLOCK_UNKNOWN_COMMAND"
    BLOCK_UNSAFE_TEXT = "BLOCK_UNSAFE_TEXT"
    BLOCK_GOVERNANCE = "BLOCK_GOVERNANCE"
    REQUIRE_CONFIRM = "REQUIRE_CONFIRM"
    SEND_HELP = "SEND_HELP"
    SKIP = "SKIP"

class TelegramCommandType(str, Enum):
    HELP = "HELP"
    STATUS = "STATUS"
    HEALTH = "HEALTH"
    SIGNALS = "SIGNALS"
    REVIEW = "REVIEW"
    PORTFOLIO = "PORTFOLIO"
    STRESS = "STRESS"
    DRIFT = "DRIFT"
    KB_SEARCH = "KB_SEARCH"
    REPORT = "REPORT"
    LAB = "LAB"
    MAINTENANCE = "MAINTENANCE"
    GOVERNANCE = "GOVERNANCE"
    DIGEST = "DIGEST"
    SETTINGS = "SETTINGS"
    UNKNOWN = "UNKNOWN"

class NotificationPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    MUTED = "MUTED"
    BLOCKED = "BLOCKED"
    ARCHIVED = "ARCHIVED"
    UNKNOWN = "UNKNOWN"

class DigestType(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    RUNTIME = "RUNTIME"
    SIGNALS = "SIGNALS"
    REVIEW = "REVIEW"
    PORTFOLIO = "PORTFOLIO"
    RISK = "RISK"
    SYSTEM = "SYSTEM"
    CUSTOM = "CUSTOM"

class TelegramCommand(BaseModel):
    command_id: str
    raw_text: str = Field(min_length=1)
    command_type: TelegramCommandType
    args: dict[str, Any] = Field(default_factory=dict)
    chat_id_hash: str
    user_id_hash: str | None = None
    received_at: datetime
    status: TelegramCommandStatus = TelegramCommandStatus.RECEIVED
    decision: TelegramCommandDecision = TelegramCommandDecision.ALLOW
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class TelegramCommandResult(BaseModel):
    result_id: str
    command_id: str
    status: TelegramCommandStatus
    decision: TelegramCommandDecision
    response_text: str
    chunks: list[str] = Field(default_factory=list)
    elapsed_seconds: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    disclaimer: str = "Telegram command result is research-only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class NotificationMessage(BaseModel):
    notification_id: str
    title: str
    body: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime
    sent_at: datetime | None = None
    channel: str = "telegram"
    source: str | None = None
    source_ref: str | None = None
    dedupe_key: str | None = None
    muted_reason: str | None = None
    retry_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DigestRequest(BaseModel):
    digest_type: DigestType
    include_signals: bool = True
    include_review: bool = True
    include_portfolio: bool = True
    include_stress: bool = True
    include_drift: bool = True
    include_lab: bool = True
    include_maintenance: bool = True
    include_governance: bool = True
    include_knowledge: bool = True
    max_items_per_section: int = 10
    send: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

class DigestResult(BaseModel):
    digest_id: str
    request: DigestRequest
    title: str
    body: str
    chunks: list[str] = Field(default_factory=list)
    notification_ids: list[str] = Field(default_factory=list)
    sent: bool = False
    blocked: bool = False
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Digest is research-only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class TelegramPermission(BaseModel):
    permission_id: str
    chat_id_hash: str
    allowed_commands: list[TelegramCommandType] = Field(default_factory=list)
    blocked_commands: list[TelegramCommandType] = Field(default_factory=list)
    is_admin: bool = False
    active: bool = True
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

class TelegramRateLimitState(BaseModel):
    key: str
    window_start: datetime
    count: int = 0
    limit: int
    reset_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
