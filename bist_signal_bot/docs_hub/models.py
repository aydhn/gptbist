from enum import Enum
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field

class DocsStatus(Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    MISSING = "MISSING"
    STALE = "STALE"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"

class DocAudience(Enum):
    USER = "USER"
    DEVELOPER = "DEVELOPER"
    OPERATOR = "OPERATOR"
    ANALYST = "ANALYST"
    QA = "QA"
    ALL = "ALL"
    UNKNOWN = "UNKNOWN"

class DocKind(Enum):
    QUICKSTART = "QUICKSTART"
    INSTALL = "INSTALL"
    ARCHITECTURE = "ARCHITECTURE"
    MODULE_GUIDE = "MODULE_GUIDE"
    CLI_REFERENCE = "CLI_REFERENCE"
    COMMAND_RECIPE = "COMMAND_RECIPE"
    TROUBLESHOOTING = "TROUBLESHOOTING"
    SECURITY = "SECURITY"
    QA = "QA"
    OPS = "OPS"
    HANDOFF = "HANDOFF"
    EXAMPLE = "EXAMPLE"
    CUSTOM = "CUSTOM"

class ArchitectureNodeType(Enum):
    MODULE = "MODULE"
    PACKAGE = "PACKAGE"
    STORE = "STORE"
    CLI_COMMAND = "CLI_COMMAND"
    CONFIG = "CONFIG"
    DOC = "DOC"
    TEST = "TEST"
    WORKFLOW = "WORKFLOW"
    INTEGRATION = "INTEGRATION"
    CUSTOM = "CUSTOM"

class TroubleshootingSeverity(Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class DocPage(BaseModel):
    page_id: str
    path: str
    title: str
    kind: DocKind
    audience: DocAudience
    summary: str
    headings: list[str]
    related_modules: list[str]
    related_commands: list[str]
    last_indexed_at: datetime
    status: DocsStatus
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DocsIndex(BaseModel):
    index_id: str
    created_at: datetime
    pages: list[DocPage]
    total_pages: int
    missing_expected_docs: list[str] = Field(default_factory=list)
    stale_docs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Documentation index is local software documentation metadata only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class DocsSearchResult(BaseModel):
    result_id: str
    query: str
    created_at: datetime
    matches: list[dict[str, Any]]
    status: DocsStatus
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ArchitectureNode(BaseModel):
    node_id: str
    node_type: ArchitectureNodeType
    label: str
    path: str | None = None
    module_name: str | None = None
    description: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class ArchitectureEdge(BaseModel):
    edge_id: str
    from_node_id: str
    to_node_id: str
    relationship: str
    description: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class ArchitectureMap(BaseModel):
    map_id: str
    created_at: datetime
    nodes: list[ArchitectureNode]
    edges: list[ArchitectureEdge]
    module_count: int
    command_count: int
    doc_count: int
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Architecture map is local software architecture metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class CommandCookbookEntry(BaseModel):
    entry_id: str
    title: str
    command: str
    purpose: str
    profile_names: list[str]
    module_names: list[str]
    expected_output: str
    risk_level: str
    requires_confirm: bool
    tags: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Command cookbook entry is local research workflow guidance only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class CommandCookbook(BaseModel):
    cookbook_id: str
    created_at: datetime
    entries: list[CommandCookbookEntry]
    profile_names: list[str]
    module_names: list[str]
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Command cookbook entry is local research workflow guidance only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class TroubleshootingEntry(BaseModel):
    entry_id: str
    title: str
    symptom: str
    likely_causes: list[str]
    checks: list[str]
    suggested_commands: list[str]
    safe_resolution_steps: list[str]
    severity: TroubleshootingSeverity
    related_modules: list[str] = Field(default_factory=list)
    related_docs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Troubleshooting entry is local software maintenance guidance only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class TroubleshootingKnowledgeBase(BaseModel):
    kb_id: str
    created_at: datetime
    entries: list[TroubleshootingEntry]
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Troubleshooting entry is local software maintenance guidance only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class DocsCoverageResult(BaseModel):
    coverage_id: str
    created_at: datetime
    expected_docs: list[str]
    existing_docs: list[str]
    missing_docs: list[str]
    modules_without_docs: list[str]
    commands_without_examples: list[str]
    docs_without_disclaimer: list[str]
    unsafe_language_findings: list[str]
    coverage_score: float | None = None
    status: DocsStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Docs coverage result is local documentation QA metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class MVPHandoffManifest(BaseModel):
    handoff_id: str
    created_at: datetime
    project_summary: str
    active_modules: list[str]
    key_commands: list[str]
    docs_index_ref: str | None = None
    architecture_map_ref: str | None = None
    qa_status: str | None = None
    ops_status: str | None = None
    bootstrap_status: str | None = None
    cli_ux_status: str | None = None
    known_limitations: list[str] = Field(default_factory=list)
    next_phase_recommendations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "MVP handoff manifest describes local research software state only. It is not investment advice, portfolio advice, or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class DocsHubReport(BaseModel):
    report_id: str
    generated_at: datetime
    docs_index: DocsIndex | None = None
    architecture_map: ArchitectureMap | None = None
    cookbook: CommandCookbook | None = None
    troubleshooting_kb: TroubleshootingKnowledgeBase | None = None
    coverage: DocsCoverageResult | None = None
    handoff: MVPHandoffManifest | None = None
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Documentation Hub report is local software metadata only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
