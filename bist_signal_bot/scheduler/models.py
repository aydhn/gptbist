from enum import Enum
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field

class MarketDayType(str, Enum):
    TRADING_DAY = "TRADING_DAY"
    WEEKEND = "WEEKEND"
    HOLIDAY = "HOLIDAY"
    HALF_DAY = "HALF_DAY"
    UNKNOWN = "UNKNOWN"

class MarketSessionType(str, Enum):
    PRE_MARKET = "PRE_MARKET"
    OPENING = "OPENING"
    INTRADAY = "INTRADAY"
    CLOSING = "CLOSING"
    POST_MARKET = "POST_MARKET"
    AFTER_HOURS = "AFTER_HOURS"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"

class ScheduleTriggerType(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    INTERVAL_MINUTES = "INTERVAL_MINUTES"
    MARKET_SESSION = "MARKET_SESSION"
    AFTER_RUNTIME = "AFTER_RUNTIME"
    MANUAL = "MANUAL"
    CUSTOM = "CUSTOM"

class ScheduledJobType(str, Enum):
    RUNTIME_RUN_ONCE = "RUNTIME_RUN_ONCE"
    DAILY_REPORT = "DAILY_REPORT"
    WEEKLY_REPORT = "WEEKLY_REPORT"
    TELEGRAM_DIGEST = "TELEGRAM_DIGEST"
    RESEARCH_LAB_PLAN = "RESEARCH_LAB_PLAN"
    DRIFT_CHECK = "DRIFT_CHECK"
    STRESS_TEST = "STRESS_TEST"
    PORTFOLIO_RESEARCH = "PORTFOLIO_RESEARCH"
    KNOWLEDGE_INDEX = "KNOWLEDGE_INDEX"
    REVIEW_FOLLOWUP_CHECK = "REVIEW_FOLLOWUP_CHECK"
    SIGNAL_EXPIRE = "SIGNAL_EXPIRE"
    MAINTENANCE_DOCTOR = "MAINTENANCE_DOCTOR"
    BACKUP_DRY_RUN = "BACKUP_DRY_RUN"
    GOVERNANCE_AUDIT = "GOVERNANCE_AUDIT"
    HEALTHCHECK = "HEALTHCHECK"
    CUSTOM = "CUSTOM"

class ScheduledJobStatus(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    DUE = "DUE"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"
    COOLDOWN = "COOLDOWN"
    UNKNOWN = "UNKNOWN"

class ScheduledJobDecision(str, Enum):
    RUN = "RUN"
    SKIP_DISABLED = "SKIP_DISABLED"
    SKIP_NOT_DUE = "SKIP_NOT_DUE"
    SKIP_MARKET_CLOSED = "SKIP_MARKET_CLOSED"
    SKIP_LOCKED = "SKIP_LOCKED"
    SKIP_COOLDOWN = "SKIP_COOLDOWN"
    BLOCK_GOVERNANCE = "BLOCK_GOVERNANCE"
    BLOCK_SECURITY = "BLOCK_SECURITY"
    DRY_RUN_ONLY = "DRY_RUN_ONLY"
    ERROR = "ERROR"

class MarketCalendarDay(BaseModel):
    date: datetime
    day_type: MarketDayType
    description: Optional[str] = None
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    half_day_close_time: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class MarketSessionSnapshot(BaseModel):
    generated_at: datetime
    local_date: datetime
    timezone: str
    day_type: MarketDayType
    session_type: MarketSessionType
    market_open: bool
    next_open_at: Optional[datetime] = None
    next_close_at: Optional[datetime] = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ScheduleTrigger(BaseModel):
    trigger_id: str
    trigger_type: ScheduleTriggerType
    timezone: str
    hour: Optional[int] = Field(default=None, ge=0, le=23)
    minute: Optional[int] = Field(default=None, ge=0, le=59)
    weekdays: list[int] = Field(default_factory=list)
    interval_minutes: Optional[int] = Field(default=None, gt=0)
    market_sessions: list[MarketSessionType] = Field(default_factory=list)
    only_trading_days: bool = False
    skip_holidays: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if not self.timezone:
            raise ValueError("timezone cannot be empty")
        for d in self.weekdays:
            if not 0 <= d <= 6:
                raise ValueError("weekdays must be between 0 and 6")

class ScheduledJob(BaseModel):
    job_id: str
    name: str
    job_type: ScheduledJobType
    status: ScheduledJobStatus
    trigger: ScheduleTrigger
    command_preview: list[str] = Field(default_factory=list)
    enabled: bool = True
    dry_run: bool = True
    requires_market_open: bool = False
    allow_after_hours: bool = True
    cooldown_minutes: int = Field(default=30, ge=0)
    max_runtime_seconds: int = Field(default=3600, gt=0)
    max_retries: int = Field(default=0, ge=0)
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.name:
            raise ValueError("name cannot be empty")

class ScheduledJobRun(BaseModel):
    run_id: str
    job_id: str
    job_name: str
    job_type: ScheduledJobType
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: ScheduledJobStatus = ScheduledJobStatus.UNKNOWN
    decision: ScheduledJobDecision = ScheduledJobDecision.ERROR
    elapsed_seconds: float = 0.0
    exit_code: Optional[int] = None
    output_refs: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    disclaimer: str = "Scheduled job run is research-only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class DueJobResult(BaseModel):
    generated_at: datetime
    session_snapshot: MarketSessionSnapshot
    due_jobs: list[ScheduledJob] = Field(default_factory=list)
    skipped_jobs: list[ScheduledJob] = Field(default_factory=list)
    blocked_jobs: list[ScheduledJob] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class SchedulerRunResult(BaseModel):
    scheduler_run_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: ScheduledJobStatus = ScheduledJobStatus.UNKNOWN
    due_result: Optional[DueJobResult] = None
    job_runs: list[ScheduledJobRun] = Field(default_factory=list)
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    blocked_count: int = 0
    elapsed_seconds: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    disclaimer: str = "Scheduler run is local research automation only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
