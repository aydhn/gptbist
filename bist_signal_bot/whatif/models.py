from enum import Enum
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class WhatIfStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class WhatIfScenarioType(str, Enum):
    BASELINE = "BASELINE"
    COST_STRESS = "COST_STRESS"
    SLIPPAGE_STRESS = "SLIPPAGE_STRESS"
    LIQUIDITY_STRESS = "LIQUIDITY_STRESS"
    CAPITAL_SCALE = "CAPITAL_SCALE"
    THRESHOLD_CHANGE = "THRESHOLD_CHANGE"
    CONSTRAINT_CHANGE = "CONSTRAINT_CHANGE"
    WEIGHTING_METHOD_CHANGE = "WEIGHTING_METHOD_CHANGE"
    REBALANCE_FREQUENCY = "REBALANCE_FREQUENCY"
    CALIBRATION_TOGGLE = "CALIBRATION_TOGGLE"
    STRATEGY_SCORE_TOGGLE = "STRATEGY_SCORE_TOGGLE"
    MONTE_CARLO_TOGGLE = "MONTE_CARLO_TOGGLE"
    CUSTOM = "CUSTOM"

class AssumptionType(str, Enum):
    COMMISSION_BPS = "COMMISSION_BPS"
    SLIPPAGE_BPS = "SLIPPAGE_BPS"
    SPREAD_BPS = "SPREAD_BPS"
    MARKET_IMPACT = "MARKET_IMPACT"
    PORTFOLIO_NOTIONAL = "PORTFOLIO_NOTIONAL"
    MAX_POSITIONS = "MAX_POSITIONS"
    MAX_SYMBOL_WEIGHT = "MAX_SYMBOL_WEIGHT"
    MAX_SECTOR_WEIGHT = "MAX_SECTOR_WEIGHT"
    MAX_TURNOVER = "MAX_TURNOVER"
    MAX_COST_DRAG = "MAX_COST_DRAG"
    CONFIDENCE_THRESHOLD = "CONFIDENCE_THRESHOLD"
    LIQUIDITY_FILTER = "LIQUIDITY_FILTER"
    WEIGHTING_METHOD = "WEIGHTING_METHOD"
    USE_CALIBRATION = "USE_CALIBRATION"
    USE_STRATEGY_SCORECARD = "USE_STRATEGY_SCORECARD"
    USE_MONTE_CARLO_SCORE = "USE_MONTE_CARLO_SCORE"
    REBALANCE_FREQUENCY = "REBALANCE_FREQUENCY"
    CUSTOM = "CUSTOM"

class SensitivityDirection(str, Enum):
    IMPROVES = "IMPROVES"
    WORSENS = "WORSENS"
    MIXED = "MIXED"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"

class WhatIfAssumptionOverride(BaseModel):
    override_id: str
    assumption_type: AssumptionType
    name: str
    old_value: Any
    new_value: Any
    unit: str | None = None
    description: str
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v

    @model_validator(mode="after")
    def validate_safe_override(self) -> "WhatIfAssumptionOverride":
        # Check for broker/order/live trading
        unsafe_keywords = ["broker", "live", "real_order", "api_key", "secret"]
        desc = self.description.lower()
        nm = self.name.lower()
        if any(k in desc for k in unsafe_keywords) or any(k in nm for k in unsafe_keywords):
            self.warnings.append("BLOCK: Override may contain unsafe broker or live trading parameters.")
        return self

class WhatIfScenario(BaseModel):
    scenario_id: str
    scenario_type: WhatIfScenarioType
    name: str
    description: str
    assumptions: list[WhatIfAssumptionOverride] = Field(default_factory=list)
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "What-if scenario is research-only. It is not investment advice or an order instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class WhatIfRunRequest(BaseModel):
    request_id: str
    source_type: str
    source_ref: str | None = None
    symbols: list[str] = Field(default_factory=list)
    strategy_names: list[str] = Field(default_factory=list)
    scenarios: list[WhatIfScenario] = Field(default_factory=list)
    baseline_required: bool = True
    save_output: bool = True
    include_portfolio_construction: bool = True
    include_portfolio_ledger: bool = True
    include_execution_costs: bool = True
    include_monte_carlo: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, v: list[str]) -> list[str]:
        return [s.upper().strip() for s in v]

    @field_validator("scenarios")
    @classmethod
    def validate_scenarios(cls, v: list[WhatIfScenario]) -> list[WhatIfScenario]:
        if not v:
            raise ValueError("At least one scenario must be provided")
        return v

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source_type cannot be empty")
        return v

class WhatIfScenarioResult(BaseModel):
    result_id: str
    scenario: WhatIfScenario
    status: WhatIfStatus
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    portfolio_score: float | None = None
    diversification_score: float | None = None
    estimated_net_quality_score: float | None = None
    estimated_total_cost_bps: float | None = None
    estimated_turnover_pct: float | None = None
    expected_signal_count: int | None = None
    selected_symbols: list[str] = Field(default_factory=list)
    constraint_violations_count: int = 0
    simulated_nav: float | None = None
    gross_return_pct: float | None = None
    net_return_pct: float | None = None
    max_drawdown_pct: float | None = None
    ruin_probability_pct: float | None = None
    warnings: list[str] = Field(default_factory=list)
    output_refs: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

class SensitivityFinding(BaseModel):
    finding_id: str
    assumption_type: AssumptionType
    metric_name: str
    baseline_value: float | None = None
    scenario_value: float | None = None
    delta_abs: float | None = None
    delta_pct: float | None = None
    direction: SensitivityDirection
    severity: str
    message: str
    recommended_action: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class WhatIfComparisonResult(BaseModel):
    comparison_id: str
    baseline_result_id: str | None = None
    scenario_results: list[WhatIfScenarioResult] = Field(default_factory=list)
    best_scenario_id: str | None = None
    worst_scenario_id: str | None = None
    sensitivity_findings: list[SensitivityFinding] = Field(default_factory=list)
    ranking: list[dict[str, Any]] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "What-if comparison is research-only. Counterfactual outcomes do not guarantee future performance. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class CapitalScalingResult(BaseModel):
    scaling_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    base_symbols: list[str] = Field(default_factory=list)
    notionals: list[float] = Field(default_factory=list)
    scenario_results: list[WhatIfScenarioResult] = Field(default_factory=list)
    capacity_warnings: list[str] = Field(default_factory=list)
    estimated_cost_curve: list[dict[str, Any]] = Field(default_factory=list)
    liquidity_breakpoints: list[dict[str, Any]] = Field(default_factory=list)
    best_research_notional: float | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Capital scaling result is research-only. It is not portfolio sizing advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class PolicySandboxResult(BaseModel):
    sandbox_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    policy_name: str
    policy_description: str
    baseline_policy: dict[str, Any] = Field(default_factory=dict)
    tested_policies: list[dict[str, Any]] = Field(default_factory=list)
    scenario_results: list[WhatIfScenarioResult] = Field(default_factory=list)
    selected_policy_candidate: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Policy sandbox result is research-only. It does not change live or real trading rules. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class WhatIfRunResult(BaseModel):
    run_id: str
    request: WhatIfRunRequest
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    elapsed_seconds: float
    status: WhatIfStatus
    scenario_results: list[WhatIfScenarioResult] = Field(default_factory=list)
    comparison: WhatIfComparisonResult | None = None
    capital_scaling: CapitalScalingResult | None = None
    policy_sandbox: PolicySandboxResult | None = None
    output_files: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    disclaimer: str = "What-if run is research-only. It is not investment advice, portfolio advice, or an order instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "scenarios_count": len(self.scenario_results),
            "generated_at": self.generated_at.isoformat(),
            "elapsed_seconds": self.elapsed_seconds
        }

    def safe_public_dict(self) -> dict[str, Any]:
        data = self.model_dump()
        if "secret" in data.get("metadata", {}):
            del data["metadata"]["secret"]
        return data
