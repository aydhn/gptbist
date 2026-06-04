import os
from pathlib import Path

def setup_dirs():
    dirs = [
        "bist_signal_bot/release_policy",
        "bist_signal_bot/tests",
        "bist_signal_bot/docs",
        "bist_signal_bot/examples",
        "bist_signal_bot/app",
        "bist_signal_bot/qa",
        "bist_signal_bot/ops",
        "bist_signal_bot/final_audit",
        "bist_signal_bot/final_handoff",
        "bist_signal_bot/maintenance_automation",
        "bist_signal_bot/performance",
        "bist_signal_bot/plugins",
        "bist_signal_bot/markets",
        "bist_signal_bot/explainability",
        "bist_signal_bot/report_templates",
        "bist_signal_bot/data_catalog",
        "bist_signal_bot/feature_store",
        "bist_signal_bot/model_registry",
        "bist_signal_bot/config_registry",
        "bist_signal_bot/docs_hub",
        "bist_signal_bot/reports",
        "bist_signal_bot/local_ui",
        "bist_signal_bot/maintenance",
        "bist_signal_bot/governance",
        "bist_signal_bot/security",
        "bist_signal_bot/config",
        "bist_signal_bot/storage",
        "bist_signal_bot/cli",
        "bist_signal_bot/core",
        "bist_signal_bot/notifications"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    Path("bist_signal_bot/release_policy/__init__.py").touch()

def append_to_file(filepath, content, before=None):
    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            f.write(content)
        return
    with open(filepath, "r") as f:
        current = f.read()
    if content.strip() in current:
        return
    if before and before in current:
        current = current.replace(before, content + "\n" + before)
    else:
        current += "\n" + content
    with open(filepath, "w") as f:
        f.write(current)

def update_exceptions():
    content = """
class ReleasePolicyError(BistSignalBotError):
    pass

class BranchPolicyError(ReleasePolicyError):
    pass

class VersionGovernanceError(ReleasePolicyError):
    pass

class CompatibilityPolicyError(ReleasePolicyError):
    pass

class ChangeControlError(ReleasePolicyError):
    pass

class ChangelogError(ReleasePolicyError):
    pass

class MigrationPolicyError(ReleasePolicyError):
    pass

class DeprecationPolicyError(ReleasePolicyError):
    pass

class ReleaseBranchFreezeError(ReleasePolicyError):
    pass

class FinalClosureError(ReleasePolicyError):
    pass

class ReleasePolicyGovernanceError(ReleasePolicyError):
    pass

class ReleasePolicyStorageError(ReleasePolicyError):
    pass
"""
    append_to_file("bist_signal_bot/core/exceptions.py", content)

def update_audit():
    content = """
    RELEASE_BRANCH_POLICIES_LOADED = "RELEASE_BRANCH_POLICIES_LOADED"
    VERSION_SNAPSHOT_CREATED = "VERSION_SNAPSHOT_CREATED"
    COMPATIBILITY_CHECK_RUN = "COMPATIBILITY_CHECK_RUN"
    CHANGE_REQUEST_CREATED = "CHANGE_REQUEST_CREATED"
    CHANGELOG_CREATED = "CHANGELOG_CREATED"
    MIGRATION_NOTES_CREATED = "MIGRATION_NOTES_CREATED"
    DEPRECATION_NOTICE_CREATED = "DEPRECATION_NOTICE_CREATED"
    RELEASE_BRANCH_FREEZE_CREATED = "RELEASE_BRANCH_FREEZE_CREATED"
    FINAL_CLOSURE_MANIFEST_CREATED = "FINAL_CLOSURE_MANIFEST_CREATED"
    RELEASE_POLICY_GOVERNANCE_ASSESSED = "RELEASE_POLICY_GOVERNANCE_ASSESSED"
    RELEASE_POLICY_REPORT_CREATED = "RELEASE_POLICY_REPORT_CREATED"
"""
    # Simply appending for mock purposes if the file doesn't exist, otherwise we just try our best.
    append_to_file("bist_signal_bot/core/audit.py", content)

def create_models():
    content = """from enum import Enum
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class ReleasePolicyStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    FROZEN = "FROZEN"
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"

class BranchKind(str, Enum):
    MAIN = "MAIN"
    DEVELOP = "DEVELOP"
    RELEASE = "RELEASE"
    HOTFIX = "HOTFIX"
    FEATURE = "FEATURE"
    EXPERIMENTAL = "EXPERIMENTAL"
    ARCHIVE = "ARCHIVE"
    UNKNOWN = "UNKNOWN"

class ChangeRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class ChangeType(str, Enum):
    FEATURE = "FEATURE"
    BUGFIX = "BUGFIX"
    REFACTOR = "REFACTOR"
    DOCS = "DOCS"
    TEST = "TEST"
    CONFIG = "CONFIG"
    SCHEMA = "SCHEMA"
    CLI_CONTRACT = "CLI_CONTRACT"
    DATA_CONTRACT = "DATA_CONTRACT"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    BREAKING = "BREAKING"
    DEPRECATION = "DEPRECATION"
    MIGRATION = "MIGRATION"
    CUSTOM = "CUSTOM"

class VersionBumpType(str, Enum):
    PATCH = "PATCH"
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    SCHEMA = "SCHEMA"
    CONFIG = "CONFIG"
    DATA_CONTRACT = "DATA_CONTRACT"
    CLI_CONTRACT = "CLI_CONTRACT"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"

class BranchPolicy(BaseModel):
    policy_id: str
    branch_kind: BranchKind
    name_pattern: str
    allowed_change_types: List[ChangeType]
    requires_qa: bool
    requires_ops: bool
    requires_final_audit: bool
    requires_changelog: bool
    requires_migration_notes: bool
    requires_compatibility_check: bool
    protected: bool
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Branch policy is local software release governance metadata only. It is not investment advice, deployment approval, or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class VersionSnapshot(BaseModel):
    snapshot_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    project_version: str
    schema_version: str
    config_version: str
    cli_contract_version: str
    data_contract_version: str
    model_registry_version: Optional[str] = None
    report_template_version: Optional[str] = None
    plugin_contract_version: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Version snapshot is local software version metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChangeRequest(BaseModel):
    change_id: str
    title: str
    description: str
    change_type: ChangeType
    risk_level: ChangeRiskLevel
    affected_modules: List[str]
    proposed_version_bump: VersionBumpType
    requires_migration: bool
    requires_deprecation_notice: bool
    requires_docs_update: bool
    requires_tests_update: bool
    status: ReleasePolicyStatus
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Change request is local software governance metadata only. It is not investment advice or trading approval. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CompatibilityCheckResult(BaseModel):
    compatibility_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    target_version: Optional[str] = None
    status: ReleasePolicyStatus
    checked_contracts: List[str]
    breaking_changes: List[str]
    schema_drift: List[str]
    cli_contract_drift: List[str]
    config_drift: List[str]
    data_contract_drift: List[str]
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Compatibility check result is local software compatibility metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChangelogEntry(BaseModel):
    entry_id: str
    version: str
    date: str
    change_type: ChangeType
    title: str
    description: str
    affected_modules: List[str]
    migration_required: bool
    deprecation_related: bool
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MigrationNote(BaseModel):
    migration_id: str
    from_version: str
    to_version: str
    title: str
    steps: List[str]
    affected_files: List[str]
    required: bool
    status: ReleasePolicyStatus
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Migration note is local software upgrade guidance only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DeprecationNotice(BaseModel):
    deprecation_id: str
    feature_name: str
    deprecated_since: str
    removal_target_version: Optional[str] = None
    replacement: Optional[str] = None
    reason: str
    status: ReleasePolicyStatus
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Deprecation notice is local software lifecycle metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReleaseBranchFreezeManifest(BaseModel):
    freeze_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    branch_name: str
    branch_kind: BranchKind
    target_version: str
    frozen: bool
    confirm: bool
    version_snapshot_id: Optional[str] = None
    compatibility_id: Optional[str] = None
    qa_status: Optional[str] = None
    ops_status: Optional[str] = None
    final_audit_status: Optional[str] = None
    final_handoff_status: Optional[str] = None
    performance_status: Optional[str] = None
    maintenance_status: Optional[str] = None
    checksum_manifest: Dict[str, str] = Field(default_factory=dict)
    blocked_changes: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Release branch freeze manifest is local release governance metadata only. It is not live deployment approval, investment advice, or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FinalClosureManifest(BaseModel):
    closure_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    project_name: str
    closure_version: str
    phase_range: str
    completed_phase_count: int
    final_status: ReleasePolicyStatus
    version_snapshot_id: Optional[str] = None
    freeze_id: Optional[str] = None
    final_audit_decision: Optional[str] = None
    final_handoff_status: Optional[str] = None
    modules_closed: List[str] = Field(default_factory=list)
    accepted_limitations: List[str] = Field(default_factory=list)
    accepted_risks: List[str] = Field(default_factory=list)
    future_roadmap_refs: List[str] = Field(default_factory=list)
    closure_notes: List[str] = Field(default_factory=list)
    no_real_order_sent: bool = True
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Final closure manifest is local software project closure metadata only. It is not investment advice, live deployment approval, or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReleasePolicyGovernanceAssessment(BaseModel):
    assessment_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: ReleasePolicyStatus
    branch_policy_status: ReleasePolicyStatus
    version_status: ReleasePolicyStatus
    compatibility_status: ReleasePolicyStatus
    changelog_status: ReleasePolicyStatus
    migration_status: ReleasePolicyStatus
    deprecation_status: ReleasePolicyStatus
    freeze_status: ReleasePolicyStatus
    closure_status: ReleasePolicyStatus
    unsafe_language_findings: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Release policy governance assessment is local release governance metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReleasePolicyReport(BaseModel):
    report_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    branch_policies: List[BranchPolicy]
    version_snapshots: List[VersionSnapshot]
    change_requests: List[ChangeRequest]
    compatibility_results: List[CompatibilityCheckResult]
    changelog_entries: List[ChangelogEntry]
    migration_notes: List[MigrationNote]
    deprecation_notices: List[DeprecationNotice]
    freezes: List[ReleaseBranchFreezeManifest]
    closures: List[FinalClosureManifest]
    governance_assessments: List[ReleasePolicyGovernanceAssessment]
    key_findings: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Release policy report is local release governance reporting only. It is not investment advice, deployment approval, or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)
"""
    with open("bist_signal_bot/release_policy/models.py", "w") as f:
        f.write(content)

if __name__ == "__main__":
    setup_dirs()
    update_exceptions()
    update_audit()
    create_models()
    print("Part 1 complete.")
