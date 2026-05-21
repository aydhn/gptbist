from enum import Enum
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class MaintenanceOperationType(str, Enum):
    BACKUP_CREATE = "BACKUP_CREATE"
    BACKUP_VERIFY = "BACKUP_VERIFY"
    RESTORE_DRY_RUN = "RESTORE_DRY_RUN"
    RESTORE_APPLY = "RESTORE_APPLY"
    RETENTION_ANALYZE = "RETENTION_ANALYZE"
    CLEANUP_DRY_RUN = "CLEANUP_DRY_RUN"
    CLEANUP_APPLY = "CLEANUP_APPLY"
    MIGRATION_PLAN = "MIGRATION_PLAN"
    MIGRATION_APPLY = "MIGRATION_APPLY"
    DOCTOR_CHECK = "DOCTOR_CHECK"
    DISASTER_RECOVERY_CHECK = "DISASTER_RECOVERY_CHECK"
    CUSTOM = "CUSTOM"


class MaintenanceStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"
    WARNING = "WARNING"
    UNKNOWN = "UNKNOWN"


class BackupScope(str, Enum):
    ALL_SAFE = "ALL_SAFE"
    MARKET_DATA = "MARKET_DATA"
    RESEARCH = "RESEARCH"
    REPORTS = "REPORTS"
    SIGNALS = "SIGNALS"
    MODELS = "MODELS"
    SCENARIOS = "SCENARIOS"
    RELEASE = "RELEASE"
    PORTFOLIO_RESEARCH = "PORTFOLIO_RESEARCH"
    STRESS = "STRESS"
    DRIFT = "DRIFT"
    RESEARCH_LAB = "RESEARCH_LAB"
    CONFIG_EXAMPLE_ONLY = "CONFIG_EXAMPLE_ONLY"
    CUSTOM = "CUSTOM"


class BackupFormat(str, Enum):
    ZIP = "ZIP"
    TAR_GZ = "TAR_GZ"
    DIRECTORY_COPY = "DIRECTORY_COPY"
    MANIFEST_ONLY = "MANIFEST_ONLY"


class RetentionTarget(str, Enum):
    LOGS = "LOGS"
    REPORTS = "REPORTS"
    RESEARCH_LEDGER = "RESEARCH_LEDGER"
    SIGNALS = "SIGNALS"
    SCENARIOS = "SCENARIOS"
    RELEASE_RUNS = "RELEASE_RUNS"
    STRESS_RESULTS = "STRESS_RESULTS"
    DRIFT_RESULTS = "DRIFT_RESULTS"
    RESEARCH_LAB_RUNS = "RESEARCH_LAB_RUNS"
    CACHE = "CACHE"
    MARKET_DATA = "MARKET_DATA"
    MODEL_ARTIFACTS = "MODEL_ARTIFACTS"
    TEMP = "TEMP"
    ALL_SAFE = "ALL_SAFE"


class MigrationStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PLANNED = "PLANNED"
    APPLIED = "APPLIED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class BackupFileEntry(BaseModel):
    relative_path: str
    size_bytes: int
    checksum_sha256: str | None = None
    scope: BackupScope
    included: bool = True
    excluded_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BackupManifest(BaseModel):
    manifest_id: str
    backup_id: str
    created_at: datetime
    app_version: str
    schema_version: str
    backup_format: BackupFormat
    scopes: list[BackupScope]
    file_entries: list[BackupFileEntry]
    total_files: int
    included_files: int
    excluded_files: int
    total_size_bytes: int
    archive_path: str | None = None
    checksum_sha256: str | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Backup manifest is operational metadata only. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "manifest_id": self.manifest_id,
            "backup_id": self.backup_id,
            "created_at": self.created_at.isoformat(),
            "format": self.backup_format.value,
            "scopes": [s.value for s in self.scopes],
            "included_files": self.included_files,
            "total_size_bytes": self.total_size_bytes,
        }


class BackupRequest(BaseModel):
    scopes: list[BackupScope] = Field(default_factory=lambda: [BackupScope.ALL_SAFE])
    backup_format: BackupFormat = BackupFormat.ZIP
    output_dir: str | None = None
    include_logs: bool = False
    include_model_artifacts: bool = False
    include_market_data: bool = True
    verify_after_create: bool = True
    dry_run: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class BackupResult(BaseModel):
    backup_id: str
    request: BackupRequest
    status: MaintenanceStatus
    manifest: BackupManifest
    output_path: str | None = None
    verified: bool = False
    elapsed_seconds: float
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    disclaimer: str = "Backup result is operational only. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)


class RestoreRequest(BaseModel):
    backup_path: str
    target_dir: str | None = None
    scopes: list[BackupScope] = Field(default_factory=lambda: [BackupScope.ALL_SAFE])
    dry_run: bool = True
    overwrite: bool = False
    verify_before_restore: bool = True
    create_pre_restore_backup: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class RestoreResult(BaseModel):
    restore_id: str
    request: RestoreRequest
    status: MaintenanceStatus
    restored_files: int = 0
    skipped_files: int = 0
    blocked_files: int = 0
    pre_restore_backup_id: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    elapsed_seconds: float
    disclaimer: str = "Restore result is operational only. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetentionPolicy(BaseModel):
    target: RetentionTarget
    keep_days: int
    keep_min_count: int = 0
    max_total_size_mb: int | None = None
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class CleanupCandidate(BaseModel):
    relative_path: str
    target: RetentionTarget
    size_bytes: int
    modified_at: datetime | None = None
    reason: str
    safe_to_delete: bool
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CleanupResult(BaseModel):
    cleanup_id: str
    status: MaintenanceStatus
    dry_run: bool
    candidates: list[CleanupCandidate]
    deleted_files: int = 0
    freed_bytes: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    elapsed_seconds: float
    disclaimer: str = "Cleanup result is operational only. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)


class MigrationPlan(BaseModel):
    migration_id: str
    from_schema_version: str
    to_schema_version: str
    status: MigrationStatus
    steps: list[dict[str, Any]] = Field(default_factory=list)
    requires_backup: bool = True
    destructive: bool = False
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MigrationResult(BaseModel):
    migration_id: str
    status: MigrationStatus
    backup_id: str | None = None
    applied_steps: int = 0
    skipped_steps: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    elapsed_seconds: float
    disclaimer: str = "Migration result is operational only. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)


class MaintenanceDoctorReport(BaseModel):
    report_id: str
    generated_at: datetime
    status: MaintenanceStatus
    checked_paths: list[str] = Field(default_factory=list)
    corrupted_files: list[str] = Field(default_factory=list)
    missing_dirs: list[str] = Field(default_factory=list)
    unsafe_files: list[str] = Field(default_factory=list)
    secret_risk_files: list[str] = Field(default_factory=list)
    schema_issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Maintenance doctor report is operational only. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
