from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

class ReleaseStage(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    ALPHA = "ALPHA"
    BETA = "BETA"
    RELEASE_CANDIDATE = "RELEASE_CANDIDATE"
    STABLE = "STABLE"
    HOTFIX = "HOTFIX"

class ReleaseStatus(str, Enum):
    READY = "READY"
    PARTIAL_READY = "PARTIAL_READY"
    NOT_READY = "NOT_READY"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"

class ReleaseCheckStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"

class ReleaseCheckCategory(str, Enum):
    IMPORTS = "IMPORTS"
    CONFIG = "CONFIG"
    HEALTHCHECK = "HEALTHCHECK"
    SECURITY = "SECURITY"
    QUALITY = "QUALITY"
    SCENARIOS = "SCENARIOS"
    PACKAGING = "PACKAGING"
    DOCS = "DOCS"
    PERFORMANCE = "PERFORMANCE"
    RUNTIME = "RUNTIME"
    MONITORING = "MONITORING"
    RESEARCH = "RESEARCH"
    REPORTS = "REPORTS"
    STORAGE = "STORAGE"
    COMPATIBILITY = "COMPATIBILITY"
    SAFETY = "SAFETY"
    CUSTOM = "CUSTOM"

class ReleaseBlockerSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ReleaseProfile(str, Enum):
    MOCK_ONLY = "MOCK_ONLY"
    LOCAL_RESEARCH = "LOCAL_RESEARCH"
    PAPER_SIMULATION = "PAPER_SIMULATION"
    RUNTIME_DRY_RUN = "RUNTIME_DRY_RUN"
    FULL_SAFE_LOCAL = "FULL_SAFE_LOCAL"
    CUSTOM = "CUSTOM"

@dataclass
class ReleaseCheckResult:
    check_id: str
    name: str
    category: ReleaseCheckCategory
    status: ReleaseCheckStatus
    severity: ReleaseBlockerSeverity
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    generated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "category": self.category.value,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message
        }

@dataclass
class ReleaseBlocker:
    blocker_id: str
    category: ReleaseCheckCategory
    severity: ReleaseBlockerSeverity
    title: str
    message: str
    blocking: bool
    remediation: list[str] = field(default_factory=list)
    related_check_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ReleaseReadinessConfig:
    stage: ReleaseStage
    profile: ReleaseProfile
    version: str
    run_healthcheck: bool = True
    run_security: bool = True
    run_quality: bool = True
    run_scenarios: bool = True
    run_packaging: bool = True
    run_docs_validation: bool = True
    run_performance_check: bool = True
    run_runtime_dry_run: bool = True
    run_report_generation: bool = True
    require_no_blockers: bool = True
    require_quality_pass: bool = True
    require_security_pass: bool = True
    require_acceptance_pass: bool = False
    save_report: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.version:
            raise ValueError("version cannot be empty")

@dataclass
class ReleaseReadinessReport:
    readiness_id: str
    config: ReleaseReadinessConfig
    status: ReleaseStatus
    readiness_score: float
    checks: list[ReleaseCheckResult] = field(default_factory=list)
    blockers: list[ReleaseBlocker] = field(default_factory=list)
    passed_count: int = 0
    warning_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    elapsed_seconds: float = 0.0
    output_files: dict[str, str] = field(default_factory=dict)
    disclaimer: str = "Release readiness output only. Research software validation. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "readiness_id": self.readiness_id,
            "status": self.status.value,
            "score": self.readiness_score,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "warnings": self.warning_count,
            "blockers": len(self.blockers)
        }

    def passed(self) -> bool:
        return self.status in [ReleaseStatus.READY, ReleaseStatus.PARTIAL_READY]

    def safe_public_dict(self) -> dict[str, Any]:
        s = self.summary()
        s["disclaimer"] = self.disclaimer
        s["version"] = self.config.version
        s["stage"] = self.config.stage.value
        s["profile"] = self.config.profile.value
        return s

@dataclass
class SafeLaunchStep:
    step_id: str
    name: str
    description: str
    command_preview: list[str]
    expected_result: str
    status: ReleaseCheckStatus
    issues: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class SafeLaunchRehearsalResult:
    rehearsal_id: str
    profile: ReleaseProfile
    steps: list[SafeLaunchStep]
    status: ReleaseStatus
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    elapsed_seconds: float = 0.0
    output_files: dict[str, str] = field(default_factory=dict)
    disclaimer: str = "Safe launch rehearsal output only. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ReleaseCandidateManifest:
    candidate_id: str
    version: str
    stage: ReleaseStage
    created_at: datetime = field(default_factory=datetime.utcnow)
    readiness_report_id: str | None = None
    package_release_id: str | None = None
    scenario_run_ids: list[str] = field(default_factory=list)
    quality_run_id: str | None = None
    security_audit_id: str | None = None
    included_artifacts: list[str] = field(default_factory=list)
    excluded_artifacts: list[str] = field(default_factory=list)
    known_issues: list[str] = field(default_factory=list)
    release_notes_path: str | None = None
    no_real_order_sent: bool = True
    disclaimer: str = "Research software release candidate. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ReleaseNotes:
    version: str
    stage: ReleaseStage
    title: str
    summary: str
    highlights: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    fixed: list[str] = field(default_factory=list)
    known_issues: list[str] = field(default_factory=list)
    safety_notes: list[str] = field(default_factory=list)
    upgrade_notes: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    disclaimer: str = "Release notes are operational documentation only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)
