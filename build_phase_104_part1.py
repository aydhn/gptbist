import os
from pathlib import Path

def ensure_file(path, content, append=False):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if append and os.path.exists(path):
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + content + "\n")
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content + "\n")

# 1. INIT
ensure_file("bist_signal_bot/synthetic_scenarios/__init__.py", "")

# 2. EXCEPTIONS
exceptions_code = """
class SyntheticScenarioError(Exception): pass
class SyntheticScenarioLibraryError(SyntheticScenarioError): pass
class SyntheticGeneratorError(SyntheticScenarioError): pass
class SyntheticOHLCVError(SyntheticGeneratorError): pass
class SyntheticMacroError(SyntheticGeneratorError): pass
class SyntheticBreadthError(SyntheticGeneratorError): pass
class SyntheticFinancialsError(SyntheticGeneratorError): pass
class SyntheticEventError(SyntheticGeneratorError): pass
class SyntheticFeatureFrameError(SyntheticGeneratorError): pass
class SyntheticStressCaseError(SyntheticScenarioError): pass
class SyntheticEdgeCaseError(SyntheticScenarioError): pass
class SyntheticScenarioManifestError(SyntheticScenarioError): pass
class SyntheticScenarioValidationError(SyntheticScenarioError): pass
class SyntheticScenarioStorageError(SyntheticScenarioError): pass
"""
ensure_file("bist_signal_bot/core/exceptions.py", exceptions_code, append=True)

# 3. SETTINGS
settings_code = """
# SYNTHETIC SCENARIOS SETTINGS
ENABLE_SYNTHETIC_SCENARIOS = True
SYNTHETIC_SCENARIOS_DIR_NAME = "synthetic_scenarios"
SYNTHETIC_SCENARIOS_RESEARCH_ONLY = True
SYNTHETIC_SCENARIOS_SAVE_RESULTS = True

SYNTHETIC_DEFAULT_SEED = 42
SYNTHETIC_DEFAULT_START_DATE = "2023-01-01"
SYNTHETIC_DEFAULT_END_DATE = "2023-12-31"
SYNTHETIC_DEFAULT_SYMBOLS = "ASELS,THYAO,GARAN,BIMAS,EREGL"
SYNTHETIC_DEFAULT_FREQUENCY = "DAILY"
SYNTHETIC_MAX_ROWS = 250000
SYNTHETIC_LARGE_SCENARIOS_ENABLED = False

SYNTHETIC_GENERATE_OHLCV = True
SYNTHETIC_GENERATE_MACRO = True
SYNTHETIC_GENERATE_BREADTH = True
SYNTHETIC_GENERATE_FINANCIALS = True
SYNTHETIC_GENERATE_EVENTS = True
SYNTHETIC_GENERATE_DISCLOSURES = True
SYNTHETIC_GENERATE_FEATURE_FRAMES = True
SYNTHETIC_GENERATE_MODEL_FIXTURES = True
SYNTHETIC_GENERATE_PORTFOLIO_OUTCOMES = True

SYNTHETIC_VALIDATE_DETERMINISM = True
SYNTHETIC_VALIDATE_OHLCV_INVARIANTS = True
SYNTHETIC_FAIL_ON_INVARIANT_BREAK = True
SYNTHETIC_REQUIRE_MANIFEST = True

SYNTHETIC_EXPORT_JSONL_ENABLED = True
SYNTHETIC_EXPORT_CSV_ENABLED = True
SYNTHETIC_EXPORT_REQUIRES_CONFIRM = True

RUNTIME_SYNTHETIC_SCENARIOS_ENABLED = True
QA_INCLUDE_SYNTHETIC_SCENARIOS = True
OPS_INCLUDE_SYNTHETIC_SCENARIOS = True
REPORT_INCLUDE_SYNTHETIC_SCENARIOS = True
RESEARCH_AUTO_LOG_SYNTHETIC_SCENARIOS = False
"""
ensure_file("bist_signal_bot/config/settings.py", settings_code, append=True)

# 4. PATHS
paths_code = """
def get_synthetic_scenarios_dir(settings=None) -> Path:
    from pathlib import Path
    return Path("data/synthetic_scenarios")
"""
ensure_file("bist_signal_bot/storage/paths.py", paths_code, append=True)

# 5. MODELS
models_code = """
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
"""
ensure_file("bist_signal_bot/synthetic_scenarios/models.py", models_code)

# 6. LIBRARY
library_code = """
from .models import SyntheticScenarioSpec, SyntheticScenarioKind, SyntheticOutputKind, SyntheticFrequency

class SyntheticScenarioLibrary:
    def default_specs(self) -> list[SyntheticScenarioSpec]:
        base_outputs = [SyntheticOutputKind.OHLCV, SyntheticOutputKind.MACRO, SyntheticOutputKind.BREADTH]
        all_outputs = list(SyntheticOutputKind)

        return [
            SyntheticScenarioSpec("trend_up_basic_v1", "Trend Up Basic", SyntheticScenarioKind.TREND_UP, "Upward trend", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("trend_down_basic_v1", "Trend Down Basic", SyntheticScenarioKind.TREND_DOWN, "Downward trend", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("range_bound_basic_v1", "Range Bound Basic", SyntheticScenarioKind.RANGE_BOUND, "Range bound", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("high_volatility_v1", "High Volatility", SyntheticScenarioKind.HIGH_VOLATILITY, "High volatility", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("low_liquidity_v1", "Low Liquidity", SyntheticScenarioKind.LOW_LIQUIDITY, "Low liquidity", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("crash_rebound_v1", "Crash Rebound", SyntheticScenarioKind.CRASH, "Crash and rebound", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("gap_events_v1", "Gap Events", SyntheticScenarioKind.GAP_UP, "Gaps", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("stale_data_v1", "Stale Data", SyntheticScenarioKind.STALE_DATA, "Stale data simulation", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("missing_data_v1", "Missing Data", SyntheticScenarioKind.MISSING_DATA, "Missing data simulation", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("schema_drift_v1", "Schema Drift", SyntheticScenarioKind.SCHEMA_DRIFT, "Schema drift simulation", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("macro_stress_v1", "Macro Stress", SyntheticScenarioKind.MACRO_STRESS, "Macro stress simulation", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("mixed_regime_v1", "Mixed Regime", SyntheticScenarioKind.MIXED_REGIME, "Mixed regimes", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, base_outputs),
            SyntheticScenarioSpec("full_pipeline_demo_v1", "Full Pipeline Demo", SyntheticScenarioKind.CUSTOM, "Full pipeline demo", ["ASELS","THYAO","GARAN","BIMAS","EREGL"], "2023-01-01", "2023-12-31", SyntheticFrequency.DAILY, 42, all_outputs),
        ]

    def get_spec(self, scenario_id_or_name: str) -> SyntheticScenarioSpec | None:
        for spec in self.default_specs():
            if spec.scenario_id == scenario_id_or_name or spec.name == scenario_id_or_name:
                return spec
        return None

    def list_specs(self, kind: SyntheticScenarioKind | None = None) -> list[SyntheticScenarioSpec]:
        specs = self.default_specs()
        if kind:
            specs = [s for s in specs if s.kind == kind]
        return specs

    def validate_spec(self, spec: SyntheticScenarioSpec) -> list[str]:
        warnings = []
        if not spec.output_kinds:
            warnings.append("No output kinds specified.")
        return warnings

    def spec_summary(self, spec: SyntheticScenarioSpec) -> dict[str, Any]:
        return {
            "scenario_id": spec.scenario_id,
            "kind": spec.kind.value,
            "symbols": spec.symbols,
            "seed": spec.seed
        }
"""
ensure_file("bist_signal_bot/synthetic_scenarios/library.py", library_code)
