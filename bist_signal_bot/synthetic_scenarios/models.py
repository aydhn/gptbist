
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

class SyntheticScenarioStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    GENERATED = "GENERATED"
    VALIDATED = "VALIDATED"
    EXPORTED = "EXPORTED"
    UNKNOWN = "UNKNOWN"

class SyntheticScenarioKind(str, Enum):
    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    RANGE_BOUND = "RANGE_BOUND"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    LOW_LIQUIDITY = "LOW_LIQUIDITY"
    GAP_UP = "GAP_UP"
    GAP_DOWN = "GAP_DOWN"
    CRASH = "CRASH"
    REBOUND = "REBOUND"
    STALE_DATA = "STALE_DATA"
    MISSING_DATA = "MISSING_DATA"
    SCHEMA_DRIFT = "SCHEMA_DRIFT"
    OUTLIER_HEAVY = "OUTLIER_HEAVY"
    EVENT_SHOCK = "EVENT_SHOCK"
    MACRO_STRESS = "MACRO_STRESS"
    MIXED_REGIME = "MIXED_REGIME"
    CUSTOM = "CUSTOM"

class SyntheticOutputKind(str, Enum):
    OHLCV = "OHLCV"
    ADJUSTED_OHLCV = "ADJUSTED_OHLCV"
    MACRO = "MACRO"
    BREADTH = "BREADTH"
    FINANCIALS = "FINANCIALS"
    EVENTS = "EVENTS"
    DISCLOSURES = "DISCLOSURES"
    FEATURE_FRAME = "FEATURE_FRAME"
    MODEL_PREDICTIONS = "MODEL_PREDICTIONS"
    CALIBRATION_OUTCOMES = "CALIBRATION_OUTCOMES"
    PORTFOLIO_OUTCOMES = "PORTFOLIO_OUTCOMES"
    REPORT_FIXTURE = "REPORT_FIXTURE"
    CUSTOM = "CUSTOM"

class SyntheticFrequency(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    CUSTOM = "CUSTOM"

@dataclass
class SyntheticScenarioSpec:
    scenario_id: str
    name: str
    kind: SyntheticScenarioKind
    description: str
    symbols: List[str]
    start_date: str
    end_date: str
    frequency: SyntheticFrequency
    seed: int
    output_kinds: List[SyntheticOutputKind]
    parameters: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = "Synthetic scenario spec describes generated local test data only. It is not real market data, investment advice, or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.name: raise ValueError("name cannot be empty")
        self.symbols = [s.upper() for s in self.symbols]
        if self.start_date > self.end_date: raise ValueError("start_date <= end_date required")

@dataclass
class SyntheticDataset:
    dataset_id: str
    scenario_id: str
    output_kind: SyntheticOutputKind
    created_at: datetime
    rows: List[Dict[str, Any]]
    row_count: int
    column_count: int
    columns: List[str]
    status: SyntheticScenarioStatus
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = "Synthetic dataset is generated local fixture data only. It is not real market data or investment advice. No real order was sent."
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SyntheticStressCase:
    stress_id: str
    scenario_id: str
    stress_name: str
    description: str
    affected_outputs: List[SyntheticOutputKind]
    severity: str
    parameters: Dict[str, Any]
    expected_findings: List[str]
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SyntheticEdgeCase:
    edge_case_id: str
    scenario_id: str
    name: str
    description: str
    target_module: str
    expected_status: str
    injected_conditions: List[str]
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SyntheticScenarioManifest:
    manifest_id: str
    scenario_id: str
    created_at: datetime
    spec: SyntheticScenarioSpec
    dataset_refs: Dict[str, str]
    output_paths: Dict[str, str]
    checksum_manifest: Dict[str, str]
    row_counts: Dict[str, int]
    validation_status: Optional[str]
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = "Synthetic scenario manifest describes generated local test artifacts only. It is not investment advice or trading approval. No real order was sent."
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SyntheticScenarioValidationResult:
    validation_id: str
    scenario_id: str
    created_at: datetime
    status: SyntheticScenarioStatus
    findings: List[str]
    failed_outputs: List[str]
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = "Synthetic scenario validation is local fixture QA metadata only. It does not certify financial correctness. No real order was sent."
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SyntheticScenarioReport:
    report_id: str
    generated_at: datetime
    specs: List[SyntheticScenarioSpec]
    datasets: List[SyntheticDataset]
    manifests: List[SyntheticScenarioManifest]
    validations: List[SyntheticScenarioValidationResult]
    stress_cases: List[SyntheticStressCase]
    edge_cases: List[SyntheticEdgeCase]
    key_findings: List[str]
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = "Synthetic scenario report is local fixture generation reporting only. It is not investment advice, market data, or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyntheticScenarioGeneratorConfig:
    ohlcv_gen: Any
    macro_gen: Any
    breadth_gen: Any
    fin_gen: Any
    evt_gen: Any
    disc_gen: Any
    feature_gen: Any
    model_fix_gen: Any
    port_gen: Any
    stress_bld: Any
    edge_fac: Any
