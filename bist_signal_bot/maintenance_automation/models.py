from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class MaintenanceStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    DRY_RUN = "DRY_RUN"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    UNKNOWN = "UNKNOWN"

class MaintenanceCadenceKind(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ON_DEMAND = "ON_DEMAND"
    CUSTOM = "CUSTOM"

class MaintenanceActionType(str, Enum):
    HEALTHCHECK = "HEALTHCHECK"
    DOCTOR = "DOCTOR"
    QA_GATE = "QA_GATE"
    OPS_READINESS = "OPS_READINESS"
    FINAL_AUDIT = "FINAL_AUDIT"
    PERFORMANCE_BENCHMARK = "PERFORMANCE_BENCHMARK"
    CACHE_CLEANUP = "CACHE_CLEANUP"
    REPORT_ROTATION = "REPORT_ROTATION"
    LOG_ROTATION = "LOG_ROTATION"
    JSONL_COMPACT = "JSONL_COMPACT"
    BACKUP_MANIFEST = "BACKUP_MANIFEST"
    STALE_ARTIFACT_CHECK = "STALE_ARTIFACT_CHECK"
    SYNTHETIC_SMOKE = "SYNTHETIC_SMOKE"
    DATA_IMPORT_CHECK = "DATA_IMPORT_CHECK"
    MARKET_REGISTRY_CHECK = "MARKET_REGISTRY_CHECK"
    EXPLAINABILITY_CHECK = "EXPLAINABILITY_CHECK"
    LOCAL_UI_CHECK = "LOCAL_UI_CHECK"
    REPORT_TEMPLATE_CHECK = "REPORT_TEMPLATE_CHECK"
    CUSTOM = "CUSTOM"

class MaintenanceArtifactKind(str, Enum):
    CACHE = "CACHE"
    REPORT = "REPORT"
    LOG = "LOG"
    JSONL_STORE = "JSONL_STORE"
    EXPORT = "EXPORT"
    MANIFEST = "MANIFEST"
    BACKUP = "BACKUP"
    TEMP_FILE = "TEMP_FILE"
    CUSTOM = "CUSTOM"

class MaintenanceAction(BaseModel):
    action_id: str
    action_type: MaintenanceActionType
    name: str
    command: Optional[str] = None
    target_path: Optional[str] = None
    required: bool = True
    destructive: bool = False
    requires_confirm: bool = False
    dry_run_supported: bool = True
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def validate_action(self) -> List[str]:
        errors = []
        if self.destructive and not self.requires_confirm:
            errors.append("Destructive actions must require confirm.")
        if self.command:
            unsafe_keywords = ["broker", "live", "order", "execute", "buy", "sell"]
            if any(k in self.command.lower() for k in unsafe_keywords):
                errors.append("Command contains unsafe/live words (broker/live/order). Action should be BLOCKED.")
        return errors

class MaintenanceCadencePolicy(BaseModel):
    policy_id: str
    name: str
    cadence: MaintenanceCadenceKind
    actions: List[MaintenanceAction]
    retention_days: Optional[int] = None
    max_cache_mb: Optional[float] = None
    max_report_age_days: Optional[int] = None
    max_log_age_days: Optional[int] = None
    enabled: bool = True
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Maintenance cadence policy is local software upkeep metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MaintenancePlan(BaseModel):
    plan_id: str
    created_at: datetime
    cadence: MaintenanceCadenceKind
    policy_id: str
    actions: List[MaintenanceAction]
    dry_run: bool = True
    confirm: bool = False
    estimated_destructive_actions: int = 0
    status: MaintenanceStatus = MaintenanceStatus.PASS
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Maintenance plan is local maintenance workflow metadata only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MaintenanceActionResult(BaseModel):
    result_id: str
    action_id: str
    action_type: MaintenanceActionType
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: MaintenanceStatus
    skipped: bool = False
    dry_run: bool = True
    affected_paths: List[str] = Field(default_factory=list)
    deleted_paths: List[str] = Field(default_factory=list)
    archived_paths: List[str] = Field(default_factory=list)
    bytes_reclaimed: Optional[int] = None
    message: str = ""
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RetentionPolicy(BaseModel):
    retention_id: str
    artifact_kind: MaintenanceArtifactKind
    path_pattern: str
    retention_days: int
    max_total_mb: Optional[float] = None
    archive_before_delete: bool = True
    requires_confirm: bool = True
    enabled: bool = True
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Retention policy is local file lifecycle metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CleanupCandidate(BaseModel):
    candidate_id: str
    artifact_kind: MaintenanceArtifactKind
    path: str
    size_bytes: Optional[int] = None
    age_days: Optional[float] = None
    reason: str
    safe_to_delete: bool = False
    requires_confirm: bool = True
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BackupManifest(BaseModel):
    backup_id: str
    created_at: datetime
    source_paths: List[str]
    backup_ref: Optional[str] = None
    checksum_manifest: Dict[str, str] = Field(default_factory=dict)
    dry_run: bool = True
    status: MaintenanceStatus = MaintenanceStatus.PASS
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Backup manifest describes local file backup metadata only. It is not investment advice, broker backup, or trading approval. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MaintenanceRunManifest(BaseModel):
    manifest_id: str
    run_id: str
    plan_id: str
    created_at: datetime
    action_result_ids: List[str]
    affected_paths: List[str] = Field(default_factory=list)
    deleted_paths: List[str] = Field(default_factory=list)
    archived_paths: List[str] = Field(default_factory=list)
    backup_manifest_id: Optional[str] = None
    checksum_manifest: Dict[str, str] = Field(default_factory=dict)
    dry_run: bool = True
    no_real_order_sent: bool = True
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Maintenance run manifest describes local maintenance artifacts only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MaintenanceRun(BaseModel):
    run_id: str
    plan: MaintenancePlan
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: MaintenanceStatus
    results: List[MaintenanceActionResult]
    manifest: Optional[MaintenanceRunManifest] = None
    key_findings: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    disclaimer: str = "Maintenance run is local software upkeep output only. It is not investment advice, portfolio advice, or a trading instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MaintenanceAutomationReport(BaseModel):
    report_id: str
    generated_at: datetime
    policies: List[MaintenanceCadencePolicy] = Field(default_factory=list)
    plans: List[MaintenancePlan] = Field(default_factory=list)
    runs: List[MaintenanceRun] = Field(default_factory=list)
    cleanup_candidates: List[CleanupCandidate] = Field(default_factory=list)
    backup_manifests: List[BackupManifest] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Maintenance automation report is local software maintenance reporting only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)
