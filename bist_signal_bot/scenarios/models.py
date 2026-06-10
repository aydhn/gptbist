from enum import Enum
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from typing import Any, Dict, List, Optional

class ScenarioType(str, Enum):
    SMOKE = "SMOKE"
    ACCEPTANCE = "ACCEPTANCE"
    E2E_RESEARCH = "E2E_RESEARCH"
    E2E_RUNTIME = "E2E_RUNTIME"
    E2E_ML = "E2E_ML"
    E2E_ADAPTIVE = "E2E_ADAPTIVE"
    SECURITY_FAILSAFE = "SECURITY_FAILSAFE"
    MONITORING_RECOVERY = "MONITORING_RECOVERY"
    PERFORMANCE_SMOKE = "PERFORMANCE_SMOKE"
    GOLDEN_REGRESSION = "GOLDEN_REGRESSION"
    CUSTOM = "CUSTOM"

class ScenarioStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"

class ScenarioStepType(str, Enum):
    COMMAND = "COMMAND"
    FUNCTION = "FUNCTION"
    DATA_FIXTURE = "DATA_FIXTURE"
    ASSERTION = "ASSERTION"
    SECURITY_CHECK = "SECURITY_CHECK"
    REPORT_CHECK = "REPORT_CHECK"
    STORAGE_CHECK = "STORAGE_CHECK"
    CLEANUP = "CLEANUP"
    CUSTOM = "CUSTOM"

class ScenarioRiskLevel(str, Enum):
    SAFE = "SAFE"
    FILE_WRITING = "FILE_WRITING"
    LONG_RUNNING = "LONG_RUNNING"
    DESTRUCTIVE_SANDBOX_ONLY = "DESTRUCTIVE_SANDBOX_ONLY"
    TELEGRAM_DRY_RUN = "TELEGRAM_DRY_RUN"
    UNKNOWN = "UNKNOWN"

class ScenarioFixtureType(str, Enum):
    MOCK_OHLCV = "MOCK_OHLCV"
    MOCK_SYMBOL_UNIVERSE = "MOCK_SYMBOL_UNIVERSE"
    MOCK_SCAN_REPORT = "MOCK_SCAN_REPORT"
    MOCK_BACKTEST_RESULT = "MOCK_BACKTEST_RESULT"
    MOCK_OPTIMIZATION_RESULT = "MOCK_OPTIMIZATION_RESULT"
    MOCK_PAPER_LEDGER = "MOCK_PAPER_LEDGER"
    MOCK_ML_MODEL = "MOCK_ML_MODEL"
    MOCK_RESEARCH_LEDGER = "MOCK_RESEARCH_LEDGER"
    MOCK_RUNTIME_STATE = "MOCK_RUNTIME_STATE"
    MOCK_MONITORING_STATE = "MOCK_MONITORING_STATE"
    CUSTOM = "CUSTOM"

class ScenarioStepConfig(BaseModel):
    step_id: str
    name: str
    step_type: ScenarioStepType
    command: Optional[List[str]] = None
    function_name: Optional[str] = None
    timeout_seconds: int
    continue_on_error: bool = False
    expected_status: Optional[ScenarioStatus] = None
    expected_exit_code: Optional[int] = None
    assertions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_step(self) -> 'ScenarioStepConfig':
        if not self.step_id:
            raise ValueError("step_id cannot be empty")
        if not self.name:
            raise ValueError("name cannot be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.step_type == ScenarioStepType.COMMAND:
            if not self.command:
                raise ValueError("command must be provided for COMMAND step type")

            allowed_binaries = {"python", "echo", "ls", "sleep", "pytest"}
            if self.command[0] not in allowed_binaries:
                raise ValueError(f"Command '{self.command[0]}' is not allowed. Allowed commands are: {', '.join(allowed_binaries)}")
        if self.step_type == ScenarioStepType.FUNCTION and not self.function_name:
            raise ValueError("function_name must be provided for FUNCTION step type")
        return self

class ScenarioConfig(BaseModel):
    scenario_id: str
    name: str
    scenario_type: ScenarioType
    description: str
    risk_level: ScenarioRiskLevel = ScenarioRiskLevel.SAFE
    symbols: List[str] = Field(default_factory=list)
    strategy_name: str = "moving_average_trend"
    source: str = "mock"
    timeframe: str = "1d"
    rows: int = 250
    steps: List[ScenarioStepConfig] = Field(default_factory=list)
    use_sandbox: bool = True
    save_outputs: bool = True
    compare_golden: bool = False
    update_golden: bool = False
    timeout_seconds: int = 600
    continue_on_error: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_scenario(self) -> 'ScenarioConfig':
        if not self.scenario_id:
            raise ValueError("scenario_id cannot be empty")
        if self.source not in ["mock", "local"]:
            raise ValueError("source must be mock or local")
        if self.rows <= 0:
            raise ValueError("rows must be positive")
        self.symbols = [s.upper().strip() for s in self.symbols if s.strip()]
        return self

class ScenarioFixture(BaseModel):
    fixture_id: str
    fixture_type: ScenarioFixtureType
    path: Optional[str] = None
    data_summary: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ScenarioStepResult(BaseModel):
    step_id: str
    name: str
    step_type: ScenarioStepType
    status: ScenarioStatus
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    elapsed_seconds: float = 0.0
    exit_code: Optional[int] = None
    stdout_tail: Optional[str] = None
    stderr_tail: Optional[str] = None
    assertions_passed: int = 0
    assertions_failed: int = 0
    issues: List[str] = Field(default_factory=list)
    output_refs: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "status": self.status.value,
            "elapsed": self.elapsed_seconds,
            "issues": self.issues
        }

class ScenarioResult(BaseModel):
    run_id: str
    scenario: ScenarioConfig
    status: ScenarioStatus
    fixtures: List[ScenarioFixture] = Field(default_factory=list)
    step_results: List[ScenarioStepResult] = Field(default_factory=list)
    golden_comparison: Optional[Dict[str, Any]] = None
    output_files: Dict[str, str] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    elapsed_seconds: float = 0.0
    warnings: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    disclaimer: str = "Scenario output only. Research/testing workflow. Not investment advice. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "scenario_id": self.scenario.scenario_id,
            "status": self.status.value,
            "elapsed": self.elapsed_seconds,
            "steps": len(self.step_results),
            "passed_steps": sum(1 for s in self.step_results if s.status == ScenarioStatus.SUCCESS),
            "issues": self.issues,
            "disclaimer": self.disclaimer
        }

    def passed(self) -> bool:
        return self.status in [ScenarioStatus.SUCCESS, ScenarioStatus.PARTIAL_SUCCESS]

    def safe_public_dict(self) -> Dict[str, Any]:
        d = self.summary()
        d["type"] = self.scenario.scenario_type.value
        return d

class GoldenSnapshot(BaseModel):
    snapshot_id: str
    scenario_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    summary: Dict[str, Any] = Field(default_factory=dict)
    normalized_output: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GoldenComparisonResult(BaseModel):
    scenario_id: str
    snapshot_id: Optional[str] = None
    status: ScenarioStatus
    matched: bool
    differences: List[Dict[str, Any]] = Field(default_factory=list)
    ignored_fields: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
