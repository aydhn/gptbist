from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

class SecurityLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    STRICT = "STRICT"

class SecurityCheckStatus(Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"

class SecurityComponent(Enum):
    CONFIG = "CONFIG"
    SECRETS = "SECRETS"
    LOGGING = "LOGGING"
    AUDIT = "AUDIT"
    NOTIFICATIONS = "NOTIFICATIONS"
    RUNTIME = "RUNTIME"
    PAPER = "PAPER"
    ML_MODEL_REGISTRY = "ML_MODEL_REGISTRY"
    FILE_SYSTEM = "FILE_SYSTEM"
    FORBIDDEN_ACTIONS = "FORBIDDEN_ACTIONS"
    CLAIMS = "CLAIMS"
    PATHS = "PATHS"
    UNKNOWN = "UNKNOWN"

class ForbiddenActionType(Enum):
    REAL_ORDER_SEND = "REAL_ORDER_SEND"
    BROKER_API_CALL = "BROKER_API_CALL"
    HTML_SCRAPING = "HTML_SCRAPING"
    PAID_API_CALL = "PAID_API_CALL"
    SECRET_LOGGING = "SECRET_LOGGING"
    UNSAFE_MODEL_LOAD = "UNSAFE_MODEL_LOAD"
    PATH_TRAVERSAL = "PATH_TRAVERSAL"
    DESTRUCTIVE_ACTION_WITHOUT_CONFIRM = "DESTRUCTIVE_ACTION_WITHOUT_CONFIRM"
    UNKNOWN = "UNKNOWN"

class KillSwitchScope(Enum):
    ALL = "ALL"
    RUNTIME = "RUNTIME"
    SCHEDULER = "SCHEDULER"
    SCANNER = "SCANNER"
    PAPER = "PAPER"
    TELEGRAM = "TELEGRAM"
    ML = "ML"
    SELF_HEALING = "SELF_HEALING"

class SecretClassification(Enum):
    TOKEN = "TOKEN"
    API_KEY = "API_KEY"
    PASSWORD = "PASSWORD"
    CHAT_ID = "CHAT_ID"
    PRIVATE_KEY = "PRIVATE_KEY"
    CONNECTION_STRING = "CONNECTION_STRING"
    UNKNOWN = "UNKNOWN"

@dataclass
class SecurityCheckResult:
    check_name: str
    component: SecurityComponent
    status: SecurityCheckStatus
    severity: SecurityLevel
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def summary(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "component": self.component.value,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "recommendations": self.recommendations,
        }

@dataclass
class SecretFinding:
    key: str
    classification: SecretClassification
    masked_value: str
    source: str
    severity: SecurityLevel
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ForbiddenActionFinding:
    action_type: ForbiddenActionType
    location: str
    message: str
    severity: SecurityLevel
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class KillSwitchState:
    enabled: bool
    scopes: list[KillSwitchScope] = field(default_factory=list)
    reason: str | None = None
    activated_at: datetime | None = None
    activated_by: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_active_for(self, scope: KillSwitchScope) -> bool:
        if not self.enabled:
            return False
        if KillSwitchScope.ALL in self.scopes:
            return True
        return scope in self.scopes

@dataclass
class SecurityAuditReport:
    status: SecurityCheckStatus
    overall_score: float
    checks: list[SecurityCheckResult] = field(default_factory=list)
    secret_findings: list[SecretFinding] = field(default_factory=list)
    forbidden_action_findings: list[ForbiddenActionFinding] = field(default_factory=list)
    kill_switch_state: KillSwitchState = field(default_factory=lambda: KillSwitchState(enabled=False))
    warnings: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    disclaimer: str = "Security audit output only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "overall_score": self.overall_score,
            "check_count": len(self.checks),
            "secret_findings_count": len(self.secret_findings),
            "forbidden_action_findings_count": len(self.forbidden_action_findings),
            "kill_switch_active": self.kill_switch_state.enabled,
            "warnings_count": len(self.warnings),
            "disclaimer": self.disclaimer
        }

    def safe_public_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "overall_score": self.overall_score,
            "check_count": len(self.checks),
            "issues_found": len(self.secret_findings) + len(self.forbidden_action_findings),
            "kill_switch_active": self.kill_switch_state.enabled,
            "generated_at": self.generated_at.isoformat(),
            "disclaimer": self.disclaimer
        }
