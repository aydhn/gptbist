from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

class ConfigValueType(str, Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    LIST_STRING = "LIST_STRING"
    JSON = "JSON"
    PATH = "PATH"
    ENUM = "ENUM"
    SECRET = "SECRET"
    UNKNOWN = "UNKNOWN"

class ConfigSafetyLevel(str, Enum):
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    SENSITIVE = "SENSITIVE"
    DANGEROUS = "DANGEROUS"
    FORBIDDEN = "FORBIDDEN"
    UNKNOWN = "UNKNOWN"

class ConfigModule(str, Enum):
    CORE = "CORE"
    DATA = "DATA"
    STRATEGY = "STRATEGY"
    SCANNER = "SCANNER"
    BACKTEST = "BACKTEST"
    ML = "ML"
    RISK = "RISK"
    TELEGRAM = "TELEGRAM"
    SCHEDULER = "SCHEDULER"
    RESEARCH_LAB = "RESEARCH_LAB"
    PERFORMANCE = "PERFORMANCE"
    DEPLOYMENT = "DEPLOYMENT"
    GOVERNANCE = "GOVERNANCE"
    MAINTENANCE = "MAINTENANCE"
    KNOWLEDGE = "KNOWLEDGE"
    REVIEW = "REVIEW"
    PORTFOLIO_RESEARCH = "PORTFOLIO_RESEARCH"
    STRESS = "STRESS"
    DRIFT = "DRIFT"
    CUSTOM = "CUSTOM"
    SYSTEM = "SYSTEM"

class FeatureFlagState(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    DRY_RUN = "DRY_RUN"
    METADATA_ONLY = "METADATA_ONLY"
    SAFE_MODE = "SAFE_MODE"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"

class RuntimeProfileType(str, Enum):
    RESEARCH_ONLY = "RESEARCH_ONLY"
    PAPER_RESEARCH = "PAPER_RESEARCH"
    SAFE_RUNTIME = "SAFE_RUNTIME"
    SCHEDULER_DRY_RUN = "SCHEDULER_DRY_RUN"
    TELEGRAM_DRY_RUN = "TELEGRAM_DRY_RUN"
    FULL_LOCAL_SAFE = "FULL_LOCAL_SAFE"
    PERFORMANCE_TEST = "PERFORMANCE_TEST"
    DEVELOPMENT = "DEVELOPMENT"
    CUSTOM = "CUSTOM"
    SYSTEM = "SYSTEM"

class ConfigValidationStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"

class ConfigChangeDecision(str, Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    REQUIRE_CONFIRM = "REQUIRE_CONFIRM"
    BLOCK_FORBIDDEN = "BLOCK_FORBIDDEN"
    BLOCK_SECRET_LEAK = "BLOCK_SECRET_LEAK"
    BLOCK_TYPE_ERROR = "BLOCK_TYPE_ERROR"
    BLOCK_GOVERNANCE = "BLOCK_GOVERNANCE"
    SKIP = "SKIP"

@dataclass
class ConfigDefinition:
    key: str
    module: ConfigModule
    value_type: ConfigValueType
    default_value: Any
    description: str
    safety_level: ConfigSafetyLevel
    required: bool = False
    secret: bool = False
    enum_values: list[str] = field(default_factory=list)
    min_value: float | None = None
    max_value: float | None = None
    deprecated: bool = False
    replacement_key: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.key:
            raise ValueError("Config key cannot be empty")
        if self.secret and self.safety_level not in [ConfigSafetyLevel.SENSITIVE, ConfigSafetyLevel.DANGEROUS, ConfigSafetyLevel.FORBIDDEN]:
            raise ValueError("Secret configs must have at least SENSITIVE safety level")
        if self.safety_level == ConfigSafetyLevel.FORBIDDEN:
            if self.default_value is not False and self.default_value is not None and self.default_value != "" and self.default_value != []:
                raise ValueError("FORBIDDEN safety level configs must default to safe false/empty values")
        if self.value_type == ConfigValueType.ENUM and not self.enum_values:
            raise ValueError("ENUM type configs must provide enum_values")

@dataclass
class ConfigValueRecord:
    key: str
    value: Any
    value_redacted: Any
    source: str
    module: ConfigModule
    value_type: ConfigValueType
    safety_level: ConfigSafetyLevel
    is_default: bool
    is_secret: bool
    valid: bool
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class FeatureFlag:
    flag_id: str
    key: str
    module: ConfigModule
    state: FeatureFlagState
    default_state: FeatureFlagState
    safety_level: ConfigSafetyLevel
    description: str
    dependencies: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    requires_confirm: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class RuntimeProfile:
    profile_id: str
    profile_type: RuntimeProfileType
    name: str
    description: str
    overrides: dict[str, Any] = field(default_factory=dict)
    feature_flags: dict[str, FeatureFlagState] = field(default_factory=dict)
    force_research_only: bool = True
    broker_enabled: bool = False
    real_order_enabled: bool = False
    telegram_send_enabled: bool = False
    scheduler_dry_run: bool = True
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.broker_enabled:
            raise ValueError("broker_enabled must be false")
        if self.real_order_enabled:
            raise ValueError("real_order_enabled must be false")
        if not self.name:
            raise ValueError("Profile name cannot be empty")
        # Ensure no secrets in overrides (basic check, comprehensive in validator)
        for k in self.overrides.keys():
            k_lower = k.lower()
            if 'token' in k_lower or 'secret' in k_lower or 'password' in k_lower or 'key' in k_lower:
                if 'public' not in k_lower:
                    raise ValueError(f"Profile overrides cannot contain secrets: {k}")

@dataclass
class ConfigValidationFinding:
    finding_id: str
    title: str
    message: str
    status: ConfigValidationStatus
    decision: ConfigChangeDecision
    key: str | None = None
    module: ConfigModule | None = None
    remediation: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ConfigValidationResult:
    validation_id: str
    generated_at: datetime
    status: ConfigValidationStatus
    records_checked: int
    findings: list[ConfigValidationFinding] = field(default_factory=list)
    blocked_count: int = 0
    warning_count: int = 0
    pass_count: int = 0
    disclaimer: str = "Config validation is operational only. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ConfigSnapshot:
    snapshot_id: str
    created_at: datetime
    records: list[ConfigValueRecord]
    flags: list[FeatureFlag]
    app_version: str = "1.0.0"
    schema_version: str = "1.0.0"
    profile_type: RuntimeProfileType | None = None
    redacted: bool = True
    checksum_sha256: str | None = None
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Config snapshot is operational metadata only. Secrets are redacted. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "created_at": self.created_at.isoformat(),
            "records_count": len(self.records),
            "flags_count": len(self.flags),
            "profile_type": self.profile_type.value if self.profile_type else None,
            "checksum": self.checksum_sha256
        }

@dataclass
class ConfigDiffItem:
    key: str
    change_type: str  # "ADDED", "REMOVED", "CHANGED"
    old_value_redacted: Any
    new_value_redacted: Any
    safety_level: ConfigSafetyLevel
    decision: ConfigChangeDecision
    module: ConfigModule | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ConfigDiffResult:
    diff_id: str
    created_at: datetime
    items: list[ConfigDiffItem]
    old_snapshot_id: str | None = None
    new_snapshot_id: str | None = None
    added_count: int = 0
    removed_count: int = 0
    changed_count: int = 0
    dangerous_count: int = 0
    blocked_count: int = 0
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Config diff is operational metadata only. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ConfigDriftResult:
    drift_id: str
    current_snapshot_id: str
    created_at: datetime
    status: ConfigValidationStatus
    drift_score: float
    drift_items: list[ConfigDiffItem] = field(default_factory=list)
    baseline_snapshot_id: str | None = None
    unexpected_enabled_flags: list[str] = field(default_factory=list)
    missing_required_keys: list[str] = field(default_factory=list)
    unsafe_changes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Config drift report is operational metadata only. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ConfigGateRequest:
    gate_name: str
    payload: dict[str, Any]
    profile_type: RuntimeProfileType | None = None
    require_research_only: bool = True
    allow_warnings: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ConfigGateResult:
    gate_id: str
    request: ConfigGateRequest
    status: ConfigValidationStatus
    decision: ConfigChangeDecision
    validation_result: ConfigValidationResult
    blocked: bool
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Config gate is operational only. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)
