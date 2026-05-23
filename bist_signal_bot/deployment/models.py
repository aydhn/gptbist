from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator

class DeploymentStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"

class DeploymentProfileType(str, Enum):
    RESEARCH_ONLY = "RESEARCH_ONLY"
    PAPER_RESEARCH = "PAPER_RESEARCH"
    TELEGRAM_DRY_RUN = "TELEGRAM_DRY_RUN"
    LOCAL_SCHEDULER_DRY_RUN = "LOCAL_SCHEDULER_DRY_RUN"
    FULL_LOCAL_SAFE = "FULL_LOCAL_SAFE"
    DEVELOPMENT = "DEVELOPMENT"
    CUSTOM = "CUSTOM"

class EnvironmentCheckType(str, Enum):
    PYTHON_VERSION = "PYTHON_VERSION"
    PACKAGE_IMPORT = "PACKAGE_IMPORT"
    FILESYSTEM = "FILESYSTEM"
    PERMISSIONS = "PERMISSIONS"
    DISK_SPACE = "DISK_SPACE"
    TIMEZONE = "TIMEZONE"
    ENV_FILE = "ENV_FILE"
    SECRET_HYGIENE = "SECRET_HYGIENE"
    CONFIG_VALIDATION = "CONFIG_VALIDATION"
    PATH_GUARD = "PATH_GUARD"
    HEALTHCHECK = "HEALTHCHECK"
    GOVERNANCE = "GOVERNANCE"
    MAINTENANCE = "MAINTENANCE"
    SCHEDULER = "SCHEDULER"
    TELEGRAM = "TELEGRAM"
    CUSTOM = "CUSTOM"

class FirstRunStepType(str, Enum):
    INIT_DIRECTORIES = "INIT_DIRECTORIES"
    CREATE_ENV_TEMPLATE = "CREATE_ENV_TEMPLATE"
    VALIDATE_CONFIG = "VALIDATE_CONFIG"
    RUN_HEALTHCHECK = "RUN_HEALTHCHECK"
    RUN_GOVERNANCE_GATE = "RUN_GOVERNANCE_GATE"
    RUN_MAINTENANCE_DOCTOR = "RUN_MAINTENANCE_DOCTOR"
    CREATE_SCHEDULER_DEFAULTS = "CREATE_SCHEDULER_DEFAULTS"
    RUN_SMOKE_TESTS = "RUN_SMOKE_TESTS"
    GENERATE_RUNBOOK = "GENERATE_RUNBOOK"
    FINAL_SUMMARY = "FINAL_SUMMARY"
    CUSTOM = "CUSTOM"

class DeploymentDecision(str, Enum):
    CONTINUE = "CONTINUE"
    WARN_CONTINUE = "WARN_CONTINUE"
    BLOCK = "BLOCK"
    REQUIRE_CONFIRM = "REQUIRE_CONFIRM"
    SKIP = "SKIP"
    ERROR = "ERROR"

class EnvironmentCheckResult(BaseModel):
    check_id: str
    check_type: EnvironmentCheckType
    status: DeploymentStatus
    decision: DeploymentDecision
    title: str
    message: str = ""
    remediation: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DeploymentProfile(BaseModel):
    profile_id: str
    profile_type: DeploymentProfileType
    name: str
    description: str = ""
    settings_overrides: Dict[str, Any] = Field(default_factory=dict)
    safe_defaults: bool = True
    telegram_send_enabled: bool = False
    scheduler_dry_run: bool = True
    broker_enabled: bool = False
    real_order_enabled: bool = False
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_safe_defaults(self):
        if self.real_order_enabled:
            raise ValueError("real_order_enabled cannot be true in deployment profiles")
        if self.broker_enabled:
            raise ValueError("broker_enabled cannot be true in deployment profiles")
        if not self.name.strip():
            raise ValueError("Profile name cannot be empty")
        return self

class EnvTemplateRequest(BaseModel):
    profile_type: DeploymentProfileType
    output_path: Optional[str] = None
    overwrite: bool = False
    include_comments: bool = True
    include_placeholders: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EnvTemplateResult(BaseModel):
    result_id: str
    status: DeploymentStatus
    output_path: Optional[str] = None
    variables_written: int = 0
    skipped_existing: bool = False
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    disclaimer: str = "Environment template output is operational only. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FirstRunStepResult(BaseModel):
    step_id: str
    step_type: FirstRunStepType
    status: DeploymentStatus
    decision: DeploymentDecision
    started_at: datetime
    finished_at: Optional[datetime] = None
    message: str = ""
    output_refs: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FirstRunResult(BaseModel):
    first_run_id: str
    profile: DeploymentProfile
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: DeploymentStatus = DeploymentStatus.UNKNOWN
    steps: List[FirstRunStepResult] = Field(default_factory=list)
    environment_checks: List[EnvironmentCheckResult] = Field(default_factory=list)
    output_files: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    disclaimer: str = "First-run setup is operational only. It does not enable real orders. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        return {
            "first_run_id": self.first_run_id,
            "status": self.status.name,
            "profile": self.profile.name,
            "steps": len(self.steps),
            "errors": len(self.errors)
        }

    def safe_public_dict(self) -> Dict[str, Any]:
        d = self.model_dump(mode="json")
        # Ensure no secrets leak
        return d

class SmokeTestResult(BaseModel):
    smoke_id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: DeploymentStatus = DeploymentStatus.UNKNOWN
    checks: List[EnvironmentCheckResult] = Field(default_factory=list)
    commands_tested: List[List[str]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    disclaimer: str = "Smoke test is operational only. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class OperatorRunbook(BaseModel):
    runbook_id: str
    profile_type: DeploymentProfileType
    created_at: datetime
    title: str
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    commands: List[List[str]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Operator runbook is operational guidance only. Not investment advice. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)
