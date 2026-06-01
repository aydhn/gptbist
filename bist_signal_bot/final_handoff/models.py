import enum
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class FinalHandoffStatus(str, enum.Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    INCOMPLETE = "INCOMPLETE"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"

class HandoffAudience(str, enum.Enum):
    USER = "USER"
    DEVELOPER = "DEVELOPER"
    OPERATOR = "OPERATOR"
    ANALYST = "ANALYST"
    QA = "QA"
    ALL = "ALL"
    UNKNOWN = "UNKNOWN"

class ReleasePackStage(str, enum.Enum):
    DRAFT = "DRAFT"
    BUILT = "BUILT"
    VERIFIED = "VERIFIED"
    FROZEN = "FROZEN"
    HANDOFF_READY = "HANDOFF_READY"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"

class RoadmapPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class MaintenanceCadence(str, enum.Enum):
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
    main_commands: List[str] = Field(default_factory=list)
    main_docs: List[str] = Field(default_factory=list)
    status: FinalHandoffStatus
    dependencies: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FinalCommandMapEntry(BaseModel):
    entry_id: str
    command: str
    category: str
    audience: HandoffAudience
    purpose: str
    safe_mode: bool = False
    dry_run_supported: bool = False
    json_supported: bool = False
    related_docs: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Command map entry is local software usage guidance only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class OperatorPlaybook(BaseModel):
    playbook_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    title: str
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    daily_routine: List[str] = Field(default_factory=list)
    weekly_routine: List[str] = Field(default_factory=list)
    monthly_routine: List[str] = Field(default_factory=list)
    emergency_checks: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Operator playbook is local software maintenance guidance only. It is not investment advice, broker operations guidance, or a trading instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DeveloperPlaybook(BaseModel):
    playbook_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    title: str
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    extension_points: List[str] = Field(default_factory=list)
    coding_standards: List[str] = Field(default_factory=list)
    test_standards: List[str] = Field(default_factory=list)
    release_standards: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Developer playbook is local software development guidance only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PostReleaseRoadmapItem(BaseModel):
    roadmap_id: str
    title: str
    description: str
    priority: RoadmapPriority
    target_area: str
    suggested_phase: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    status: FinalHandoffStatus
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MaintenanceTask(BaseModel):
    task_id: str
    title: str
    cadence: MaintenanceCadence
    command_hint: str
    owner_area: str
    expected_output: str
    requires_confirm: bool = False
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Maintenance task is local software upkeep guidance only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FinalReleasePack(BaseModel):
    pack_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    stage: ReleasePackStage
    release_candidate_id: Optional[str] = None
    go_no_go_decision: Optional[str] = None
    included_docs: List[str] = Field(default_factory=list)
    included_examples: List[str] = Field(default_factory=list)
    included_reports: List[str] = Field(default_factory=list)
    included_manifests: List[str] = Field(default_factory=list)
    command_map_ref: Optional[str] = None
    operator_playbook_ref: Optional[str] = None
    developer_playbook_ref: Optional[str] = None
    roadmap_ref: Optional[str] = None
    checksum_manifest: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Final release pack describes local research software handoff artifacts only. It is not investment advice, live deployment approval, or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FinalHandoffManifest(BaseModel):
    handoff_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    project_name: str
    project_summary: str
    final_status: FinalHandoffStatus
    release_pack_id: Optional[str] = None
    release_candidate_id: Optional[str] = None
    go_no_go_decision: Optional[str] = None
    module_summaries: List[FinalModuleSummary] = Field(default_factory=list)
    command_entries: List[FinalCommandMapEntry] = Field(default_factory=list)
    operator_playbook_id: Optional[str] = None
    developer_playbook_id: Optional[str] = None
    roadmap_items: List[PostReleaseRoadmapItem] = Field(default_factory=list)
    maintenance_tasks: List[MaintenanceTask] = Field(default_factory=list)
    known_limitations: List[str] = Field(default_factory=list)
    residual_risks: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Final handoff manifest is local software project handoff metadata only. It is not financial advice, investment advice, or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FinalHandoffReport(BaseModel):
    report_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    manifest: Optional[FinalHandoffManifest] = None
    release_pack: Optional[FinalReleasePack] = None
    operator_playbook: Optional[OperatorPlaybook] = None
    developer_playbook: Optional[DeveloperPlaybook] = None
    roadmap_items: List[PostReleaseRoadmapItem] = Field(default_factory=list)
    maintenance_tasks: List[MaintenanceTask] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Final handoff report is local software release documentation only. It is not investment advice, portfolio advice, or a trading instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)
