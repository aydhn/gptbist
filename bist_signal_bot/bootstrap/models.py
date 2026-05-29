from enum import Enum
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class BootstrapStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    NOT_STARTED = "NOT_STARTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class RunProfileName(str, Enum):
    MINIMAL = "MINIMAL"
    STANDARD = "STANDARD"
    FULL_RESEARCH = "FULL_RESEARCH"
    QA = "QA"
    DEMO = "DEMO"
    SAFE_MAINTENANCE = "SAFE_MAINTENANCE"
    CUSTOM = "CUSTOM"

class BootstrapCheckType(str, Enum):
    PYTHON_VERSION = "PYTHON_VERSION"
    PACKAGE_IMPORT = "PACKAGE_IMPORT"
    CONFIG = "CONFIG"
    PATHS = "PATHS"
    STORAGE = "STORAGE"
    FIXTURES = "FIXTURES"
    SECURITY = "SECURITY"
    NO_EXTERNAL_CALLS = "NO_EXTERNAL_CALLS"
    NO_REAL_ORDER = "NO_REAL_ORDER"
    QA = "QA"
    OPS = "OPS"
    DOCS = "DOCS"
    CLI = "CLI"
    CUSTOM = "CUSTOM"

class CommandRecipeType(str, Enum):
    QUICKSTART = "QUICKSTART"
    OFFLINE_DEMO = "OFFLINE_DEMO"
    MINIMAL_SCAN = "MINIMAL_SCAN"
    CONTEXT_REVIEW = "CONTEXT_REVIEW"
    PORTFOLIO_RESEARCH = "PORTFOLIO_RESEARCH"
    QA_RELEASE_GATE = "QA_RELEASE_GATE"
    OPS_HEALTH = "OPS_HEALTH"
    DATA_IMPORT = "DATA_IMPORT"
    REPORTING = "REPORTING"
    CUSTOM = "CUSTOM"

class RunProfile(BaseModel):
    profile_id: str
    name: RunProfileName
    title: str
    description: str
    enabled_modules: list[str] = Field(default_factory=list)
    disabled_modules: list[str] = Field(default_factory=list)
    env_overrides: dict[str, str] = Field(default_factory=dict)
    default_commands: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Run profile is local research configuration metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class BootstrapCheckResult(BaseModel):
    check_id: str
    check_type: BootstrapCheckType
    name: str
    status: BootstrapStatus
    message: str
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class BootstrapInitResult(BaseModel):
    init_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile: RunProfile
    base_dir: str
    created_paths: list[str] = Field(default_factory=list)
    config_files: list[str] = Field(default_factory=list)
    fixture_files: list[str] = Field(default_factory=list)
    status: BootstrapStatus
    checks: list[BootstrapCheckResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Bootstrap init prepares local research folders only. It is not investment advice or trading setup approval. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class BootstrapValidationResult(BaseModel):
    validation_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile_name: Optional[RunProfileName] = None
    status: BootstrapStatus
    checks: list[BootstrapCheckResult] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Bootstrap validation is local software readiness metadata only. It is not financial or trading readiness. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class OfflineDemoRun(BaseModel):
    demo_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile: RunProfileName
    commands_run: list[str] = Field(default_factory=list)
    command_results: list[dict[str, Any]] = Field(default_factory=list)
    artifacts_created: dict[str, str] = Field(default_factory=dict)
    status: BootstrapStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Offline demo uses synthetic/local data only. It does not represent real market performance and is not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class CommandRecipeStep(BaseModel):
    step_id: str
    order: int
    title: str
    command: str
    description: str
    expected_output: Optional[str] = None
    destructive: bool = False
    requires_confirm: bool = False
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class CommandRecipe(BaseModel):
    recipe_id: str
    recipe_type: CommandRecipeType
    title: str
    description: str
    steps: list[CommandRecipeStep] = Field(default_factory=list)
    estimated_complexity: str
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Command recipe is local research workflow guidance only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ReleaseBundleManifest(BaseModel):
    bundle_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile_name: RunProfileName
    project_version: Optional[str] = None
    schema_version: str
    included_modules: list[str] = Field(default_factory=list)
    included_docs: list[str] = Field(default_factory=list)
    included_examples: list[str] = Field(default_factory=list)
    qa_gate_status: Optional[str] = None
    ops_readiness_status: Optional[str] = None
    reproducibility_pack_ref: Optional[str] = None
    checksums: dict[str, str] = Field(default_factory=dict)
    status: BootstrapStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Release bundle manifest describes local research software artifacts only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class OnboardingGuide(BaseModel):
    guide_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile_name: RunProfileName
    title: str
    sections: list[dict[str, Any]] = Field(default_factory=list)
    recommended_recipes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Onboarding guide is local software setup guidance only."
    metadata: dict[str, Any] = Field(default_factory=dict)

class BootstrapReport(BaseModel):
    report_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    init_result: Optional[BootstrapInitResult] = None
    validation_result: Optional[BootstrapValidationResult] = None
    demo_runs: list[OfflineDemoRun] = Field(default_factory=list)
    recipes: list[CommandRecipe] = Field(default_factory=list)
    release_bundle: Optional[ReleaseBundleManifest] = None
    onboarding_guide: Optional[OnboardingGuide] = None
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Bootstrap report is local software setup reporting only. It is not investment advice, portfolio advice, or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
