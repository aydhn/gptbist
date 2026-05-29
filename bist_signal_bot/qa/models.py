from enum import Enum
from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime

class QAStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class QACheckType(str, Enum):
    UNIT = "UNIT"
    INTEGRATION = "INTEGRATION"
    E2E = "E2E"
    CLI_SMOKE = "CLI_SMOKE"
    REGRESSION = "REGRESSION"
    SECURITY = "SECURITY"
    SAFETY_LANGUAGE = "SAFETY_LANGUAGE"
    NO_EXTERNAL_CALLS = "NO_EXTERNAL_CALLS"
    NO_REAL_ORDER = "NO_REAL_ORDER"
    CONFIG_VALIDATION = "CONFIG_VALIDATION"
    DOCS = "DOCS"
    REPRODUCIBILITY = "REPRODUCIBILITY"
    RELEASE_GATE = "RELEASE_GATE"
    CUSTOM = "CUSTOM"

class QAModuleName(str, Enum):
    CORE = "CORE"
    DATA = "DATA"
    SCANNER = "SCANNER"
    SIGNALS = "SIGNALS"
    BACKTESTING = "BACKTESTING"
    VALIDATION = "VALIDATION"
    CALIBRATION = "CALIBRATION"
    STRATEGY_REGISTRY = "STRATEGY_REGISTRY"
    EXECUTION_SIM = "EXECUTION_SIM"
    RISK = "RISK"
    PORTFOLIO_CONSTRUCTION = "PORTFOLIO_CONSTRUCTION"
    PORTFOLIO_LEDGER = "PORTFOLIO_LEDGER"
    WHATIF = "WHATIF"
    EVENTS = "EVENTS"
    DISCLOSURES = "DISCLOSURES"
    FINANCIALS = "FINANCIALS"
    VALUATION = "VALUATION"
    FACTORS = "FACTORS"
    BREADTH = "BREADTH"
    MACRO = "MACRO"
    CONTEXT_FUSION = "CONTEXT_FUSION"
    REVIEW_WORKFLOW = "REVIEW_WORKFLOW"
    REPORTS = "REPORTS"
    SECURITY = "SECURITY"
    CLI = "CLI"
    RUNTIME = "RUNTIME"
    CUSTOM = "CUSTOM"

class QAFixtureKind(str, Enum):
    OHLCV = "OHLCV"
    INSTRUMENTS = "INSTRUMENTS"
    MACRO = "MACRO"
    EVENTS = "EVENTS"
    DISCLOSURES = "DISCLOSURES"
    FINANCIALS = "FINANCIALS"
    PORTFOLIO = "PORTFOLIO"
    SIGNALS = "SIGNALS"
    CONFIG = "CONFIG"
    EXPECTED_OUTPUT = "EXPECTED_OUTPUT"
    CUSTOM = "CUSTOM"

class QAScenarioKind(str, Enum):
    BASELINE = "BASELINE"
    STRONG_TECHNICAL_SUPPORT = "STRONG_TECHNICAL_SUPPORT"
    HIGH_SCORE_HIGH_RISK = "HIGH_SCORE_HIGH_RISK"
    MACRO_STRESS = "MACRO_STRESS"
    BREADTH_DIVERGENCE = "BREADTH_DIVERGENCE"
    EVENT_BLACKOUT = "EVENT_BLACKOUT"
    DISCLOSURE_HIGH_SEVERITY = "DISCLOSURE_HIGH_SEVERITY"
    WEAK_FINANCIAL_QUALITY = "WEAK_FINANCIAL_QUALITY"
    EXTREME_VALUATION = "EXTREME_VALUATION"
    FACTOR_CROWDING = "FACTOR_CROWDING"
    PORTFOLIO_CONCENTRATION = "PORTFOLIO_CONCENTRATION"
    MISSING_DATA = "MISSING_DATA"
    STALE_CONTEXT = "STALE_CONTEXT"
    CUSTOM = "CUSTOM"

class ReleaseGateDecision(str, Enum):
    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    NOT_READY = "NOT_READY"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"

class QAFixtureManifest(BaseModel):
    manifest_id: str
    created_at: datetime
    fixture_root: str
    fixtures: dict[str, str] = Field(default_factory=dict)
    symbols: list[str] = Field(default_factory=list)
    date_range: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class QAScenario(BaseModel):
    scenario_id: str
    scenario_kind: QAScenarioKind
    name: str
    description: str
    fixture_refs: list[str] = Field(default_factory=list)
    expected_modules: list[QAModuleName] = Field(default_factory=list)
    expected_status: QAStatus
    expected_warnings: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "QA scenario is synthetic research test metadata only. It is not investment advice and does not represent real market performance."
    metadata: dict[str, Any] = Field(default_factory=dict)

class QACheckResult(BaseModel):
    check_id: str
    check_type: QACheckType
    module_name: QAModuleName
    name: str
    status: QAStatus
    started_at: datetime
    finished_at: datetime | None = None
    elapsed_seconds: float | None = None
    message: str = ""
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    output_refs: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

class SmokeTestResult(BaseModel):
    smoke_id: str
    created_at: datetime
    command: str
    exit_code: int | None = None
    status: QAStatus
    stdout_excerpt: str | None = None
    stderr_excerpt: str | None = None
    elapsed_seconds: float | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class RegressionMatrixItem(BaseModel):
    item_id: str
    module_name: QAModuleName
    check_type: QACheckType
    test_name: str
    required_for_release: bool
    expected_status: QAStatus
    latest_status: QAStatus | None = None
    owner: str | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class RegressionMatrixResult(BaseModel):
    matrix_id: str
    created_at: datetime
    items: list[RegressionMatrixItem] = Field(default_factory=list)
    total_count: int = 0
    pass_count: int = 0
    watch_count: int = 0
    fail_count: int = 0
    blocked_count: int = 0
    status: QAStatus = QAStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ReleaseGateResult(BaseModel):
    gate_id: str
    created_at: datetime
    decision: ReleaseGateDecision
    status: QAStatus
    check_results: list[QACheckResult] = Field(default_factory=list)
    smoke_results: list[SmokeTestResult] = Field(default_factory=list)
    regression_matrix: RegressionMatrixResult | None = None
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    release_notes: list[str] = Field(default_factory=list)
    disclaimer: str = "Release gate result is software QA metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ReproducibilityPack(BaseModel):
    pack_id: str
    created_at: datetime
    run_manifest_path: str | None = None
    config_snapshot_path: str | None = None
    fixture_manifest_path: str | None = None
    environment_summary_path: str | None = None
    qa_report_path: str | None = None
    checksum_manifest: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class QAReport(BaseModel):
    report_id: str
    generated_at: datetime
    fixture_manifest: QAFixtureManifest | None = None
    scenarios: list[QAScenario] = Field(default_factory=list)
    check_results: list[QACheckResult] = Field(default_factory=list)
    smoke_results: list[SmokeTestResult] = Field(default_factory=list)
    regression_matrix: RegressionMatrixResult | None = None
    release_gate: ReleaseGateResult | None = None
    reproducibility_pack: ReproducibilityPack | None = None
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "QA report is software quality metadata only. It is not investment advice, portfolio advice, or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
