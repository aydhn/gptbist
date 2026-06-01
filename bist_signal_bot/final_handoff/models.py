from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class FinalHandoffStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    INCOMPLETE = "INCOMPLETE"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"

class HandoffAudience(str, Enum):
    USER = "USER"
    DEVELOPER = "DEVELOPER"
    OPERATOR = "OPERATOR"
    ANALYST = "ANALYST"
    QA = "QA"
    ALL = "ALL"
    UNKNOWN = "UNKNOWN"

class ReleasePackStage(str, Enum):
    DRAFT = "DRAFT"
    BUILT = "BUILT"
    VERIFIED = "VERIFIED"
    FROZEN = "FROZEN"
    HANDOFF_READY = "HANDOFF_READY"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"

class RoadmapPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class MaintenanceCadence(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ON_DEMAND = "ON_DEMAND"
    UNKNOWN = "UNKNOWN"

class FinalModuleSummary(BaseModel):
    module_id: str
    module_name: str
    title: str
    purpose: str
    owner_area: str
    main_commands: list[str] = Field(default_factory=list)
    main_docs: list[str] = Field(default_factory=list)
    status: FinalHandoffStatus
    dependencies: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class FinalCommandMapEntry(BaseModel):
    entry_id: str
    command: str
    category: str
    audience: HandoffAudience
    purpose: str
    safe_mode: bool
    dry_run_supported: bool
    json_supported: bool
    related_docs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Command map entry is local software usage guidance only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class OperatorPlaybook(BaseModel):
    playbook_id: str
    created_at: datetime
    title: str
    sections: list[dict[str, Any]] = Field(default_factory=list)
    daily_routine: list[str] = Field(default_factory=list)
    weekly_routine: list[str] = Field(default_factory=list)
    monthly_routine: list[str] = Field(default_factory=list)
    emergency_checks: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Operator playbook is local software maintenance guidance only. It is not investment advice, broker operations guidance, or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class DeveloperPlaybook(BaseModel):
    playbook_id: str
    created_at: datetime
    title: str
    sections: list[dict[str, Any]] = Field(default_factory=list)
    extension_points: list[str] = Field(default_factory=list)
    coding_standards: list[str] = Field(default_factory=list)
    test_standards: list[str] = Field(default_factory=list)
    release_standards: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Developer playbook is local software development guidance only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class PostReleaseRoadmapItem(BaseModel):
    roadmap_id: str
    title: str
    description: str
    priority: RoadmapPriority
    target_area: str
    suggested_phase: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    status: FinalHandoffStatus
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class MaintenanceTask(BaseModel):
    task_id: str
    title: str
    cadence: MaintenanceCadence
    command_hint: str
    owner_area: str
    expected_output: str
    requires_confirm: bool
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Maintenance task is local software upkeep guidance only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class FinalReleasePack(BaseModel):
    pack_id: str
    created_at: datetime
    stage: ReleasePackStage
    release_candidate_id: str | None = None
    go_no_go_decision: str | None = None
    included_docs: list[str] = Field(default_factory=list)
    included_examples: list[str] = Field(default_factory=list)
    included_reports: list[str] = Field(default_factory=list)
    included_manifests: list[str] = Field(default_factory=list)
    command_map_ref: str | None = None
    operator_playbook_ref: str | None = None
    developer_playbook_ref: str | None = None
    roadmap_ref: str | None = None
    checksum_manifest: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Final release pack describes local research software handoff artifacts only. It is not investment advice, live deployment approval, or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class FinalHandoffManifest(BaseModel):
    handoff_id: str
    created_at: datetime
    project_name: str
    project_summary: str
    final_status: FinalHandoffStatus
    release_pack_id: str | None = None
    release_candidate_id: str | None = None
    go_no_go_decision: str | None = None
    module_summaries: list[FinalModuleSummary] = Field(default_factory=list)
    command_entries: list[FinalCommandMapEntry] = Field(default_factory=list)
    operator_playbook_id: str | None = None
    developer_playbook_id: str | None = None
    roadmap_items: list[PostReleaseRoadmapItem] = Field(default_factory=list)
    maintenance_tasks: list[MaintenanceTask] = Field(default_factory=list)
    known_limitations: list[str] = Field(default_factory=list)
    residual_risks: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Final handoff manifest is local software project handoff metadata only. It is not financial advice, investment advice, or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class FinalHandoffReport(BaseModel):
    report_id: str
    generated_at: datetime
    manifest: FinalHandoffManifest | None = None
    release_pack: FinalReleasePack | None = None
    operator_playbook: OperatorPlaybook | None = None
    developer_playbook: DeveloperPlaybook | None = None
    roadmap_items: list[PostReleaseRoadmapItem] = Field(default_factory=list)
    maintenance_tasks: list[MaintenanceTask] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Final handoff report is local software release documentation only. It is not investment advice, portfolio advice, or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
