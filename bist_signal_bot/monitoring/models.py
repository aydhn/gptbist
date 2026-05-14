from enum import Enum
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator

class HealthLevel(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class AlertSeverity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class AlertStatus(Enum):
    NEW = "NEW"
    SENT = "SENT"
    THROTTLED = "THROTTLED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"

class MonitoringComponent(Enum):
    RUNTIME = "RUNTIME"
    SCHEDULER = "SCHEDULER"
    DATA = "DATA"
    SCANNER = "SCANNER"
    STRATEGY = "STRATEGY"
    RISK = "RISK"
    PORTFOLIO_RISK = "PORTFOLIO_RISK"
    REGIME = "REGIME"
    ML = "ML"
    PAPER = "PAPER"
    TELEGRAM = "TELEGRAM"
    STORAGE = "STORAGE"
    LOCK = "LOCK"
    CONFIG = "CONFIG"
    HEALTHCHECK = "HEALTHCHECK"
    UNKNOWN = "UNKNOWN"

class MetricType(Enum):
    COUNTER = "COUNTER"
    GAUGE = "GAUGE"
    TIMER = "TIMER"
    STATUS = "STATUS"
    EVENT = "EVENT"

class SelfHealingActionType(Enum):
    CLEAR_STALE_LOCK = "CLEAR_STALE_LOCK"
    RESET_RUNTIME_STATE = "RESET_RUNTIME_STATE"
    ROTATE_BACKUP = "ROTATE_BACKUP"
    CLEAN_TEMP_FILES = "CLEAN_TEMP_FILES"
    VALIDATE_STORAGE = "VALIDATE_STORAGE"
    DISABLE_RUNTIME_LOOP = "DISABLE_RUNTIME_LOOP"
    NOOP = "NOOP"
    UNKNOWN = "UNKNOWN"

class DiagnosticCheckStatus(Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"

class HeartbeatRecord(BaseModel):
    heartbeat_id: str = Field(...)
    timestamp: datetime = Field(...)
    component: MonitoringComponent = Field(...)
    status: HealthLevel = Field(...)
    message: str = Field(...)
    runtime_run_id: str | None = Field(default=None)
    scheduler_active: bool = Field(default=False)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_heartbeat(self):
        if not self.heartbeat_id:
            raise ValueError("heartbeat_id cannot be empty")
        if self.message is None:
            raise ValueError("message cannot be None")
        return self

class MonitoringMetric(BaseModel):
    metric_id: str = Field(...)
    timestamp: datetime = Field(...)
    component: MonitoringComponent = Field(...)
    name: str = Field(...)
    metric_type: MetricType = Field(...)
    value: float | int | str | bool | None = Field(...)
    unit: str | None = Field(default=None)
    tags: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_metric(self):
        if not self.metric_id:
            raise ValueError("metric_id cannot be empty")
        if not self.name:
            raise ValueError("name cannot be empty")
        if not isinstance(self.tags, dict):
            raise ValueError("tags must be a dict")
        return self

class MonitoringAlert(BaseModel):
    alert_id: str = Field(...)
    timestamp: datetime = Field(...)
    component: MonitoringComponent = Field(...)
    severity: AlertSeverity = Field(...)
    status: AlertStatus = Field(...)
    title: str = Field(...)
    message: str = Field(...)
    fingerprint: str = Field(...)
    count: int = Field(default=1)
    first_seen_at: datetime = Field(...)
    last_seen_at: datetime = Field(...)
    sent_at: datetime | None = Field(default=None)
    resolved_at: datetime | None = Field(default=None)
    runtime_run_id: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_alert(self):
        if not self.title:
            raise ValueError("title cannot be empty")
        if not self.fingerprint:
            raise ValueError("fingerprint cannot be empty")
        if self.count <= 0:
            raise ValueError("count must be positive")
        return self

class DiagnosticCheckResult(BaseModel):
    check_name: str
    component: MonitoringComponent
    status: DiagnosticCheckStatus
    severity: AlertSeverity
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    generated_at: datetime

    def summary(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "component": self.component.value,
            "status": self.status.value,
            "message": self.message,
            "generated_at": self.generated_at.isoformat()
        }

class MonitoringSnapshot(BaseModel):
    generated_at: datetime
    overall_health: HealthLevel
    heartbeats: list[HeartbeatRecord]
    metrics: list[MonitoringMetric]
    active_alerts: list[MonitoringAlert]
    diagnostics: list[DiagnosticCheckResult]
    runtime_state_summary: dict[str, Any]
    latest_run_summary: dict[str, Any] | None = None
    issues: list[str] = Field(default_factory=list)
    disclaimer: str = Field(default="Monitoring output only. Not investment advice. No real order was sent.")
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "overall_health": self.overall_health.value,
            "issues": self.issues,
            "disclaimer": self.disclaimer
        }

class SelfHealingAction(BaseModel):
    action_id: str
    action_type: SelfHealingActionType
    component: MonitoringComponent
    description: str
    requires_confirm: bool
    safe_to_auto_run: bool
    executed: bool = False
    success: bool | None = None
    message: str | None = None
    generated_at: datetime
    executed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class SelfHealingResult(BaseModel):
    actions: list[SelfHealingAction]
    executed_count: int
    success_count: int
    failed_count: int
    skipped_count: int
    generated_at: datetime
    disclaimer: str = Field(default="Self-healing output only. Operational repair actions only. No real order was sent.")
    metadata: dict[str, Any] = Field(default_factory=dict)
