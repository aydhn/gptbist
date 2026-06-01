from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

class FinalAuditStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"

class FinalCheckType(str, Enum):
    IMPORT_CHECK = "IMPORT_CHECK"
    HEALTHCHECK = "HEALTHCHECK"
    CLI_CONTRACT = "CLI_CONTRACT"
    JSON_SCHEMA = "JSON_SCHEMA"
    QA_GATE = "QA_GATE"
    OPS_READINESS = "OPS_READINESS"
    BOOTSTRAP_VALIDATION = "BOOTSTRAP_VALIDATION"
    DOCS_COVERAGE = "DOCS_COVERAGE"
    DATA_QUALITY = "DATA_QUALITY"
    FEATURE_LEAKAGE = "FEATURE_LEAKAGE"
    MODEL_GOVERNANCE = "MODEL_GOVERNANCE"
    MONITORING_HEALTH = "MONITORING_HEALTH"
    LEADERBOARD_RANKING = "LEADERBOARD_RANKING"
    ORCHESTRATOR_DRY_RUN = "ORCHESTRATOR_DRY_RUN"
    SECURITY = "SECURITY"
    SAFE_LANGUAGE = "SAFE_LANGUAGE"
    NO_REAL_ORDER = "NO_REAL_ORDER"
    ACCEPTANCE = "ACCEPTANCE"
    CUSTOM = "CUSTOM"

class ReleaseDecision(str, Enum):
    GO = "GO"
    GO_WITH_WARNINGS = "GO_WITH_WARNINGS"
    NO_GO = "NO_GO"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"

class ReleaseCandidateStage(str, Enum):
    DRAFT = "DRAFT"
    CANDIDATE = "CANDIDATE"
    FROZEN = "FROZEN"
    APPROVED_RESEARCH = "APPROVED_RESEARCH"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"

class FinalAuditCheckResult(BaseModel):
    check_id: str
    check_type: FinalCheckType
    module_name: str
    name: str
    status: FinalAuditStatus
    started_at: datetime
    finished_at: datetime | None = None
    elapsed_seconds: float | None = None
    message: str = ""
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    output_refs: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

class FinalAcceptanceSuite(BaseModel):
    suite_id: str
    created_at: datetime
    name: str
    checks: list[FinalAuditCheckResult] = Field(default_factory=list)
    total_count: int = 0
    pass_count: int = 0
    watch_count: int = 0
    fail_count: int = 0
    blocked_count: int = 0
    status: FinalAuditStatus = FinalAuditStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Final acceptance suite is local software QA metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class FinalIntegrationMatrixItem(BaseModel):
    item_id: str
    source_module: str
    target_module: str
    integration_name: str
    required: bool = True
    latest_status: FinalAuditStatus = FinalAuditStatus.UNKNOWN
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class FinalIntegrationMatrix(BaseModel):
    matrix_id: str
    created_at: datetime
    items: list[FinalIntegrationMatrixItem] = Field(default_factory=list)
    total_count: int = 0
    failing_required_count: int = 0
    blocked_count: int = 0
    status: FinalAuditStatus = FinalAuditStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Final integration matrix is local software metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class FinalSecurityAuditResult(BaseModel):
    audit_id: str
    created_at: datetime
    safe_language_status: FinalAuditStatus = FinalAuditStatus.UNKNOWN
    no_real_order_status: FinalAuditStatus = FinalAuditStatus.UNKNOWN
    no_broker_status: FinalAuditStatus = FinalAuditStatus.UNKNOWN
    no_external_calls_status: FinalAuditStatus = FinalAuditStatus.UNKNOWN
    path_safety_status: FinalAuditStatus = FinalAuditStatus.UNKNOWN
    secret_redaction_status: FinalAuditStatus = FinalAuditStatus.UNKNOWN
    blocked_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Final security audit is local software safety metadata only. It is not investment advice or trading approval. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ReleaseCandidateManifest(BaseModel):
    candidate_id: str
    created_at: datetime
    stage: ReleaseCandidateStage = ReleaseCandidateStage.DRAFT
    project_version: str | None = None
    schema_version: str = "1.0"
    included_modules: list[str] = Field(default_factory=list)
    module_statuses: dict[str, str] = Field(default_factory=dict)
    qa_status: str | None = None
    ops_status: str | None = None
    bootstrap_status: str | None = None
    cli_ux_status: str | None = None
    docs_hub_status: str | None = None
    data_catalog_status: str | None = None
    feature_store_status: str | None = None
    model_registry_status: str | None = None
    monitoring_status: str | None = None
    leaderboard_status: str | None = None
    orchestrator_status: str | None = None
    acceptance_suite_id: str | None = None
    integration_matrix_id: str | None = None
    security_audit_id: str | None = None
    checksum_manifest: dict[str, str] = Field(default_factory=dict)
    known_limitations: list[str] = Field(default_factory=list)
    residual_risks: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Release candidate manifest describes local research software artifacts only. It is not investment advice, live deployment approval, or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class HardeningFreezeManifest(BaseModel):
    freeze_id: str
    candidate_id: str
    created_at: datetime
    frozen: bool = False
    frozen_paths: list[str] = Field(default_factory=list)
    config_snapshot_ref: str | None = None
    docs_snapshot_ref: str | None = None
    test_summary_ref: str | None = None
    checksum_manifest: dict[str, str] = Field(default_factory=dict)
    blocked_changes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Hardening freeze manifest is local release governance metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class GoNoGoDecision(BaseModel):
    decision_id: str
    candidate_id: str
    created_at: datetime
    decision: ReleaseDecision = ReleaseDecision.UNKNOWN
    status: FinalAuditStatus = FinalAuditStatus.UNKNOWN
    blocking_reasons: list[str] = Field(default_factory=list)
    warning_reasons: list[str] = Field(default_factory=list)
    required_checks_passed: bool = False
    security_passed: bool = False
    docs_passed: bool = False
    qa_passed: bool = False
    ops_passed: bool = False
    acceptance_passed: bool = False
    final_notes: list[str] = Field(default_factory=list)
    disclaimer: str = "Go/No-Go decision is local software release governance metadata only. It is not financial, investment, or trading readiness. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class FinalRiskRegisterItem(BaseModel):
    risk_id: str
    title: str
    description: str
    severity: str
    status: FinalAuditStatus = FinalAuditStatus.UNKNOWN
    owner_module: str | None = None
    mitigation: str | None = None
    accepted: bool = False
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class FinalAuditReport(BaseModel):
    report_id: str
    generated_at: datetime
    acceptance_suite: FinalAcceptanceSuite | None = None
    integration_matrix: FinalIntegrationMatrix | None = None
    security_audit: FinalSecurityAuditResult | None = None
    release_candidate: ReleaseCandidateManifest | None = None
    freeze_manifest: HardeningFreezeManifest | None = None
    go_no_go: GoNoGoDecision | None = None
    risk_register: list[FinalRiskRegisterItem] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Final audit report is local software release reporting only. It is not investment advice, portfolio advice, or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
