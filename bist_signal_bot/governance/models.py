from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class GovernanceStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"

class GovernanceSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class GovernanceDomain(str, Enum):
    RESEARCH_ONLY = "RESEARCH_ONLY"
    FINANCIAL_CLAIMS = "FINANCIAL_CLAIMS"
    REAL_ORDER_SAFETY = "REAL_ORDER_SAFETY"
    BROKER_API = "BROKER_API"
    SECRET_HYGIENE = "SECRET_HYGIENE"
    PAID_SERVICES = "PAID_SERVICES"
    HTML_SCRAPING = "HTML_SCRAPING"
    TELEGRAM_SAFETY = "TELEGRAM_SAFETY"
    DATA_PRIVACY = "DATA_PRIVACY"
    BACKUP_RESTORE = "BACKUP_RESTORE"
    RELEASE_READINESS = "RELEASE_READINESS"
    RUNTIME = "RUNTIME"
    RESEARCH_LAB = "RESEARCH_LAB"
    REPORTS = "REPORTS"
    AUDIT_LOG = "AUDIT_LOG"
    CUSTOM = "CUSTOM"

class GovernanceDecision(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    BLOCK = "BLOCK"
    REQUIRE_CONFIRM = "REQUIRE_CONFIRM"
    REQUIRE_REDACTION = "REQUIRE_REDACTION"
    SKIP = "SKIP"
    REVIEW_MANUALLY = "REVIEW_MANUALLY"

class GovernanceRuleType(str, Enum):
    REQUIRED_DISCLAIMER = "REQUIRED_DISCLAIMER"
    FORBIDDEN_PATTERN = "FORBIDDEN_PATTERN"
    REQUIRED_SETTING = "REQUIRED_SETTING"
    SECRET_SCAN = "SECRET_SCAN"
    CLAIM_SCAN = "CLAIM_SCAN"
    PATH_SAFETY = "PATH_SAFETY"
    AUDIT_COMPLETENESS = "AUDIT_COMPLETENESS"
    OUTPUT_REDACTION = "OUTPUT_REDACTION"
    CONFIRM_REQUIRED = "CONFIRM_REQUIRED"
    CUSTOM = "CUSTOM"

class GovernanceRule(BaseModel):
    rule_id: str
    name: str
    domain: GovernanceDomain
    rule_type: GovernanceRuleType
    severity: GovernanceSeverity
    enabled: bool = True
    blocking: bool = False
    pattern: str | None = None
    expected_setting: str | None = None
    expected_value: str | bool | int | float | None = None
    description: str
    remediation: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class GovernanceFinding(BaseModel):
    finding_id: str
    rule_id: str
    domain: GovernanceDomain
    severity: GovernanceSeverity
    status: GovernanceStatus
    decision: GovernanceDecision
    title: str
    message: str
    evidence_refs: list[str] = Field(default_factory=list)
    remediation: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

class GovernancePolicy(BaseModel):
    policy_id: str
    version: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    rules: list[GovernanceRule] = Field(default_factory=list)
    require_research_only: bool = True
    block_real_order_language: bool = True
    block_broker_api: bool = True
    block_paid_services: bool = True
    block_html_scraping: bool = True
    require_secret_redaction: bool = True
    require_confirm_for_policy_update: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

class AuditReviewRequest(BaseModel):
    domains: list[GovernanceDomain] = Field(default_factory=list)
    start_date: datetime | None = None
    end_date: datetime | None = None
    include_research_ledger: bool = True
    include_audit_log: bool = True
    include_reports: bool = True
    include_release: bool = True
    include_runtime: bool = True
    include_maintenance: bool = True
    save_output: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

class AuditReviewResult(BaseModel):
    review_id: str
    request: AuditReviewRequest
    status: GovernanceStatus
    findings: list[GovernanceFinding] = Field(default_factory=list)
    reviewed_events: int = 0
    reviewed_reports: int = 0
    reviewed_research_runs: int = 0
    blocked_count: int = 0
    warning_count: int = 0
    pass_count: int = 0
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    elapsed_seconds: float = 0.0
    output_files: dict[str, str] = Field(default_factory=dict)
    disclaimer: str = "Audit review is operational governance output only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class GovernanceGateRequest(BaseModel):
    gate_name: str
    domains: list[GovernanceDomain] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)
    require_pass: bool = True
    allow_warnings: bool = True
    save_output: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

class GovernanceGateResult(BaseModel):
    gate_id: str
    request: GovernanceGateRequest
    status: GovernanceStatus
    decision: GovernanceDecision
    findings: list[GovernanceFinding] = Field(default_factory=list)
    blocked: bool = False
    warnings: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    elapsed_seconds: float = 0.0
    disclaimer: str = "Governance gate result is operational only. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class EvidencePackRequest(BaseModel):
    pack_name: str
    include_audit_log: bool = True
    include_research_ledger: bool = True
    include_release_reports: bool = True
    include_scenario_results: bool = True
    include_maintenance_reports: bool = True
    include_policy: bool = True
    include_settings_snapshot: bool = True
    output_dir: str | None = None
    dry_run: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

class EvidencePackManifest(BaseModel):
    pack_id: str
    pack_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    files: list[dict[str, Any]] = Field(default_factory=list)
    excluded_files: list[dict[str, Any]] = Field(default_factory=list)
    checksum_sha256: str | None = None
    archive_path: str | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Evidence pack is operational metadata only. It contains no trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ComplianceAttestation(BaseModel):
    attestation_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    policy_version: str
    status: GovernanceStatus
    statements: list[str] = Field(default_factory=list)
    findings_summary: dict[str, Any] = Field(default_factory=dict)
    evidence_pack_id: str | None = None
    signed_by: str | None = None
    disclaimer: str = "Compliance attestation is an internal operational statement only. It is not legal advice, investment advice, or a regulatory certification. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
