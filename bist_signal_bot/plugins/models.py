from enum import Enum
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field

class PluginStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    VALIDATED = "VALIDATED"
    LOADED = "LOADED"
    ACTIVE = "ACTIVE"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    DISABLED = "DISABLED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"

class PluginKind(str, Enum):
    STRATEGY = "STRATEGY"
    SIGNAL = "SIGNAL"
    INDICATOR = "INDICATOR"
    FEATURE = "FEATURE"
    DATA_IMPORT_ADAPTER = "DATA_IMPORT_ADAPTER"
    REPORT_SECTION = "REPORT_SECTION"
    SYNTHETIC_SCENARIO = "SYNTHETIC_SCENARIO"
    MARKET_DEFINITION = "MARKET_DEFINITION"
    VALIDATION_RULE = "VALIDATION_RULE"
    MAINTENANCE_ACTION = "MAINTENANCE_ACTION"
    LOCAL_UI_PAGE = "LOCAL_UI_PAGE"
    ORCHESTRATOR_TASK = "ORCHESTRATOR_TASK"
    CUSTOM = "CUSTOM"

class PluginCapabilityKind(str, Enum):
    READ_LOCAL_FILES = "READ_LOCAL_FILES"
    WRITE_LOCAL_FILES = "WRITE_LOCAL_FILES"
    READ_CONFIG = "READ_CONFIG"
    REGISTER_STRATEGY = "REGISTER_STRATEGY"
    REGISTER_FEATURE = "REGISTER_FEATURE"
    REGISTER_REPORT_SECTION = "REGISTER_REPORT_SECTION"
    REGISTER_DATA_ADAPTER = "REGISTER_DATA_ADAPTER"
    REGISTER_MARKET = "REGISTER_MARKET"
    REGISTER_SYNTHETIC_SCENARIO = "REGISTER_SYNTHETIC_SCENARIO"
    REGISTER_VALIDATION_RULE = "REGISTER_VALIDATION_RULE"
    REGISTER_UI_PAGE = "REGISTER_UI_PAGE"
    RUN_DRY_RUN_COMMAND = "RUN_DRY_RUN_COMMAND"
    EXTERNAL_NETWORK = "EXTERNAL_NETWORK"
    BROKER_ACCESS = "BROKER_ACCESS"
    ORDER_EXECUTION = "ORDER_EXECUTION"
    CLOUD_API = "CLOUD_API"
    CUSTOM = "CUSTOM"

class PluginHookKind(str, Enum):
    ON_REGISTER = "ON_REGISTER"
    ON_VALIDATE = "ON_VALIDATE"
    ON_TEST = "ON_TEST"
    ON_REPORT = "ON_REPORT"
    STRATEGY_DISCOVERY = "STRATEGY_DISCOVERY"
    SIGNAL_DISCOVERY = "SIGNAL_DISCOVERY"
    FEATURE_COMPUTE = "FEATURE_COMPUTE"
    DATA_IMPORT_PREVIEW = "DATA_IMPORT_PREVIEW"
    REPORT_SECTION_RENDER = "REPORT_SECTION_RENDER"
    SYNTHETIC_GENERATE = "SYNTHETIC_GENERATE"
    MARKET_REGISTER = "MARKET_REGISTER"
    VALIDATION_RULE_RUN = "VALIDATION_RULE_RUN"
    MAINTENANCE_ACTION_RUN = "MAINTENANCE_ACTION_RUN"
    LOCAL_UI_PAGE_RENDER = "LOCAL_UI_PAGE_RENDER"
    ORCHESTRATOR_TASK_RUN = "ORCHESTRATOR_TASK_RUN"
    CUSTOM = "CUSTOM"

class PluginExecutionMode(str, Enum):
    DISABLED = "DISABLED"
    SAFE_METADATA_ONLY = "SAFE_METADATA_ONLY"
    DRY_RUN = "DRY_RUN"
    LOCAL_EXECUTE = "LOCAL_EXECUTE"
    TEST_ONLY = "TEST_ONLY"
    UNKNOWN = "UNKNOWN"

class PluginManifest(BaseModel):
    plugin_id: str
    name: str
    version: str
    kind: PluginKind
    entrypoint: str | None = None
    module_path: str | None = None
    description: str
    author: str | None = None
    compatible_with: list[str] = Field(default_factory=list)
    requested_capabilities: list[PluginCapabilityKind] = Field(default_factory=list)
    hooks: list[PluginHookKind] = Field(default_factory=list)
    enabled: bool = False
    checksum: str | None = None
    created_at: datetime | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Plugin manifest is local extension metadata only. It is not investment advice, live deployment approval, or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class PluginCapabilityAssessment(BaseModel):
    assessment_id: str
    plugin_id: str
    created_at: datetime
    requested_capabilities: list[PluginCapabilityKind] = Field(default_factory=list)
    allowed_capabilities: list[PluginCapabilityKind] = Field(default_factory=list)
    blocked_capabilities: list[PluginCapabilityKind] = Field(default_factory=list)
    status: PluginStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Plugin capability assessment is local safety metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class PluginContract(BaseModel):
    contract_id: str
    kind: PluginKind
    required_fields: list[str] = Field(default_factory=list)
    required_hooks: list[PluginHookKind] = Field(default_factory=list)
    allowed_capabilities: list[PluginCapabilityKind] = Field(default_factory=list)
    required_tests: list[str] = Field(default_factory=list)
    version: str
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class PluginHookRegistration(BaseModel):
    registration_id: str
    plugin_id: str
    hook_kind: PluginHookKind
    handler_ref: str | None = None
    priority: int = 100
    enabled: bool = False
    status: PluginStatus
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class PluginValidationResult(BaseModel):
    validation_id: str
    plugin_id: str
    created_at: datetime
    status: PluginStatus
    manifest_valid: bool
    contract_valid: bool
    capabilities_valid: bool
    hooks_valid: bool
    sandbox_valid: bool
    findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Plugin validation result is local extension QA metadata only. It is not investment advice or trading approval. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class PluginTestResult(BaseModel):
    test_id: str
    plugin_id: str
    created_at: datetime
    status: PluginStatus
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    dry_run: bool = True
    findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    disclaimer: str = "Plugin test result is local dry-run test metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class PluginLoadResult(BaseModel):
    load_id: str
    plugin_id: str
    created_at: datetime
    execution_mode: PluginExecutionMode
    loaded: bool
    registered_hooks: list[PluginHookRegistration] = Field(default_factory=list)
    status: PluginStatus
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    disclaimer: str = "Plugin load result is local extension loading metadata only. It is not live deployment approval or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class PluginGovernanceAssessment(BaseModel):
    governance_id: str
    plugin_id: str
    created_at: datetime
    status: PluginStatus
    manifest_status: PluginStatus
    capability_status: PluginStatus
    validation_status: PluginStatus
    test_status: PluginStatus | None = None
    unsafe_language_findings: list[str] = Field(default_factory=list)
    blocked_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Plugin governance assessment is local extension governance metadata only. It is not investment advice, broker approval, or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class PluginRegistryReport(BaseModel):
    report_id: str
    generated_at: datetime
    manifests: list[PluginManifest] = Field(default_factory=list)
    contracts: list[PluginContract] = Field(default_factory=list)
    validations: list[PluginValidationResult] = Field(default_factory=list)
    test_results: list[PluginTestResult] = Field(default_factory=list)
    load_results: list[PluginLoadResult] = Field(default_factory=list)
    governance_assessments: list[PluginGovernanceAssessment] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Plugin registry report is local extension governance reporting only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
