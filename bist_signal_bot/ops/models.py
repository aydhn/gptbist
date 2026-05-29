
from enum import Enum
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field

class OpsStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class OpsSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class OpsCheckType(str, Enum):
    HEALTH = "HEALTH"
    STORE_INTEGRITY = "STORE_INTEGRITY"
    STALENESS = "STALENESS"
    CONFIG = "CONFIG"
    SCHEDULER = "SCHEDULER"
    QA_GATE = "QA_GATE"
    SECURITY = "SECURITY"
    BACKUP = "BACKUP"
    RESTORE = "RESTORE"
    RETENTION = "RETENTION"
    MIGRATION = "MIGRATION"
    REPORTING = "REPORTING"
    CUSTOM = "CUSTOM"

class OpsIncidentType(str, Enum):
    STORE_CORRUPTION = "STORE_CORRUPTION"
    STALE_DATA = "STALE_DATA"
    CONFIG_INVALID = "CONFIG_INVALID"
    QA_GATE_BLOCKED = "QA_GATE_BLOCKED"
    SCHEDULER_FAILURE = "SCHEDULER_FAILURE"
    REPORT_FAILURE = "REPORT_FAILURE"
    BACKUP_FAILURE = "BACKUP_FAILURE"
    RESTORE_FAILURE = "RESTORE_FAILURE"
    MIGRATION_REQUIRED = "MIGRATION_REQUIRED"
    SECURITY_GUARD_FAILURE = "SECURITY_GUARD_FAILURE"
    SAFE_LANGUAGE_FAILURE = "SAFE_LANGUAGE_FAILURE"
    UNKNOWN = "UNKNOWN"

class OpsRunbookType(str, Enum):
    STORE_REPAIR = "STORE_REPAIR"
    STALE_DATA_REFRESH = "STALE_DATA_REFRESH"
    CONFIG_FIX = "CONFIG_FIX"
    QA_FAILURE_TRIAGE = "QA_FAILURE_TRIAGE"
    SCHEDULER_RESTART = "SCHEDULER_RESTART"
    BACKUP_RETRY = "BACKUP_RETRY"
    RESTORE_DRY_RUN = "RESTORE_DRY_RUN"
    MIGRATION_CHECK = "MIGRATION_CHECK"
    SECURITY_REVIEW = "SECURITY_REVIEW"
    REPORT_REBUILD = "REPORT_REBUILD"
    GENERAL_DIAGNOSTIC = "GENERAL_DIAGNOSTIC"
    CUSTOM = "CUSTOM"

class BackupScope(str, Enum):
    CONFIG = "CONFIG"
    DATA = "DATA"
    REPORTS = "REPORTS"
    RESEARCH = "RESEARCH"
    PORTFOLIO = "PORTFOLIO"
    CONTEXT = "CONTEXT"
    REVIEW = "REVIEW"
    QA = "QA"
    ALL = "ALL"
    CUSTOM = "CUSTOM"

class RetentionAction(str, Enum):
    KEEP = "KEEP"
    ARCHIVE = "ARCHIVE"
    DELETE_DRY_RUN = "DELETE_DRY_RUN"
    DELETE_CONFIRMED = "DELETE_CONFIRMED"
    COMPRESS = "COMPRESS"
    SKIP = "SKIP"
    UNKNOWN = "UNKNOWN"

class OpsCheckResult(BaseModel):
    check_id: str
    check_type: OpsCheckType
    module_name: str
    status: OpsStatus
    severity: OpsSeverity
    started_at: datetime
    finished_at: datetime | None = None
    elapsed_seconds: float | None = None
    message: str
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    output_refs: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

class OpsHealthSnapshot(BaseModel):
    snapshot_id: str
    created_at: datetime
    status: OpsStatus
    checks: list[OpsCheckResult] = Field(default_factory=list)
    pass_count: int = 0
    watch_count: int = 0
    fail_count: int = 0
    blocked_count: int = 0
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Ops health snapshot is local software reliability metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class StoreIntegrityResult(BaseModel):
    result_id: str
    created_at: datetime
    root_path: str
    files_checked: int = 0
    jsonl_files_checked: int = 0
    invalid_files: list[str] = Field(default_factory=list)
    invalid_lines: list[dict[str, Any]] = Field(default_factory=list)
    orphan_files: list[str] = Field(default_factory=list)
    missing_expected_files: list[str] = Field(default_factory=list)
    status: OpsStatus
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class StalenessFinding(BaseModel):
    finding_id: str
    module_name: str
    object_type: str
    object_id: str | None = None
    last_updated_at: datetime | None = None
    stale_days: int | None = None
    threshold_days: int
    status: OpsStatus
    severity: OpsSeverity
    message: str
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class OpsIncident(BaseModel):
    incident_id: str
    incident_type: OpsIncidentType
    status: OpsStatus
    severity: OpsSeverity
    title: str
    description: str
    detected_at: datetime
    resolved_at: datetime | None = None
    related_check_ids: list[str] = Field(default_factory=list)
    related_files: list[str] = Field(default_factory=list)
    runbook_type: OpsRunbookType | None = None
    resolution_note: str | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Ops incident is local software/research operations metadata only. It is not a trading incident or investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class OpsRunbookStep(BaseModel):
    step_id: str
    runbook_type: OpsRunbookType
    title: str
    description: str
    command_hint: str | None = None
    destructive: bool = False
    requires_confirm: bool = False
    status: OpsStatus = OpsStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class OpsRunbook(BaseModel):
    runbook_id: str
    runbook_type: OpsRunbookType
    title: str
    description: str
    steps: list[OpsRunbookStep] = Field(default_factory=list)
    related_incident_id: str | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Ops runbook is local maintenance guidance only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class BackupManifest(BaseModel):
    backup_id: str
    created_at: datetime
    scope: list[BackupScope] = Field(default_factory=list)
    source_root: str
    backup_path: str
    files_included: int = 0
    total_bytes: int = 0
    checksum_manifest: dict[str, str] = Field(default_factory=dict)
    status: OpsStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Backup manifest covers local research artifacts only. It is not broker/account backup. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class RestorePlan(BaseModel):
    restore_id: str
    created_at: datetime
    backup_id: str | None = None
    backup_path: str
    target_root: str
    dry_run: bool = True
    files_to_restore: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    checksum_status: OpsStatus
    status: OpsStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Restore plan is local research artifact recovery metadata only. It is not broker/account recovery. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class RetentionFinding(BaseModel):
    finding_id: str
    path: str
    module_name: str | None = None
    age_days: int | None = None
    size_bytes: int | None = None
    action: RetentionAction
    dry_run: bool = True
    reason: str
    status: OpsStatus
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class MigrationCheckResult(BaseModel):
    migration_id: str
    created_at: datetime
    current_schema_version: str | None = None
    expected_schema_version: str | None = None
    modules_checked: list[str] = Field(default_factory=list)
    migrations_required: list[str] = Field(default_factory=list)
    incompatible_items: list[str] = Field(default_factory=list)
    status: OpsStatus
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class OperationalReadinessResult(BaseModel):
    readiness_id: str
    created_at: datetime
    status: OpsStatus
    health_snapshot: OpsHealthSnapshot | None = None
    store_integrity: StoreIntegrityResult | None = None
    latest_qa_gate_status: str | None = None
    backup_status: OpsStatus | None = None
    open_incidents: list[OpsIncident] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Operational readiness is software reliability metadata only. It is not financial, investment, or trading readiness. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class OpsReport(BaseModel):
    report_id: str
    generated_at: datetime
    health_snapshot: OpsHealthSnapshot | None = None
    store_integrity: StoreIntegrityResult | None = None
    staleness_findings: list[StalenessFinding] = Field(default_factory=list)
    incidents: list[OpsIncident] = Field(default_factory=list)
    runbooks: list[OpsRunbook] = Field(default_factory=list)
    backups: list[BackupManifest] = Field(default_factory=list)
    restore_plans: list[RestorePlan] = Field(default_factory=list)
    retention_findings: list[RetentionFinding] = Field(default_factory=list)
    migration_check: MigrationCheckResult | None = None
    readiness: OperationalReadinessResult | None = None
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Ops report is local software reliability reporting only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
