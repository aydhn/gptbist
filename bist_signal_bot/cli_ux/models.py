from datetime import datetime
from enum import Enum, IntEnum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class CLIStatus(str, Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"

class CLIOutputMode(str, Enum):
    TEXT = "TEXT"
    JSON = "JSON"
    TABLE = "TABLE"
    MARKDOWN = "MARKDOWN"
    QUIET = "QUIET"
    VERBOSE = "VERBOSE"
    UNKNOWN = "UNKNOWN"

class CLIExitCode(IntEnum):
    SUCCESS = 0
    WARNING = 1
    USER_ERROR = 2
    VALIDATION_ERROR = 3
    NOT_FOUND = 4
    SAFETY_BLOCKED = 5
    CONFIRM_REQUIRED = 6
    CONFIG_ERROR = 7
    IO_ERROR = 8
    INTERNAL_ERROR = 10

class CommandRiskLevel(str, Enum):
    SAFE_READ_ONLY = "SAFE_READ_ONLY"
    WRITES_LOCAL = "WRITES_LOCAL"
    DESTRUCTIVE_LOCAL = "DESTRUCTIVE_LOCAL"
    REQUIRES_CONFIRM = "REQUIRES_CONFIRM"
    BLOCKED_UNSAFE = "BLOCKED_UNSAFE"
    UNKNOWN = "UNKNOWN"

class CommandContractType(str, Enum):
    HEALTHCHECK = "HEALTHCHECK"
    SCANNER = "SCANNER"
    CONTEXT = "CONTEXT"
    REVIEW_WORKFLOW = "REVIEW_WORKFLOW"
    PORTFOLIO = "PORTFOLIO"
    REPORT = "REPORT"
    QA = "QA"
    OPS = "OPS"
    BOOTSTRAP = "BOOTSTRAP"
    WORKFLOW = "WORKFLOW"
    CUSTOM = "CUSTOM"

class CLIOutputEnvelope(BaseModel):
    envelope_id: str
    created_at: datetime
    command: str
    status: CLIStatus
    exit_code: int
    output_mode: CLIOutputMode
    payload: Dict[str, Any]
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    disclaimer: str = "CLI output is local research software output only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CLICommandContract(BaseModel):
    contract_id: str
    command_path: str
    contract_type: CommandContractType
    description: str
    output_schema_name: str
    stable_fields: List[str] = Field(default_factory=list)
    optional_fields: List[str] = Field(default_factory=list)
    exit_codes: Dict[str, int] = Field(default_factory=dict)
    risk_level: CommandRiskLevel
    supports_json: bool = True
    supports_dry_run: bool = False
    supports_confirm: bool = False
    examples: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CLIOutputSchema(BaseModel):
    schema_id: str
    name: str
    version: str
    schema_obj: Dict[str, Any] = Field(default_factory=dict, alias="schema")
    required_fields: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True

class CLIErrorMessage(BaseModel):
    error_id: str
    error_type: str
    command: Optional[str] = None
    user_message: str
    technical_message: Optional[str] = None
    suggested_fix: Optional[str] = None
    docs_ref: Optional[str] = None
    exit_code: int
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CLIAlias(BaseModel):
    alias_id: str
    alias: str
    target_command: str
    description: str
    deprecated: bool = False
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowStepResult(BaseModel):
    step_id: str
    order: int
    command: str
    status: CLIStatus
    exit_code: Optional[int] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    elapsed_seconds: Optional[float] = None
    output_ref: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowRun(BaseModel):
    run_id: str
    created_at: datetime
    workflow_name: str
    profile_name: Optional[str] = None
    steps: List[WorkflowStepResult] = Field(default_factory=list)
    status: CLIStatus
    exit_code: int
    artifacts: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    disclaimer: str = "Workflow run is local research automation only. It is not investment advice or an order instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CLICompatibilityResult(BaseModel):
    result_id: str
    created_at: datetime
    contracts_checked: int = 0
    compatible_count: int = 0
    drift_count: int = 0
    missing_count: int = 0
    status: CLIStatus
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CLIUXReport(BaseModel):
    report_id: str
    generated_at: datetime
    contracts: List[CLICommandContract] = Field(default_factory=list)
    schemas: List[CLIOutputSchema] = Field(default_factory=list)
    aliases: List[CLIAlias] = Field(default_factory=list)
    workflow_runs: List[WorkflowRun] = Field(default_factory=list)
    compatibility: Optional[CLICompatibilityResult] = None
    key_findings: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "CLI UX report is local software usability metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)
