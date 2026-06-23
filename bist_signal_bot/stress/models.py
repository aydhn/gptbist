import uuid
from enum import Enum
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class StressInputType(str, Enum):
    PORTFOLIO_RESEARCH_SNAPSHOT = "PORTFOLIO_RESEARCH_SNAPSHOT"
    BASKET_SIMULATION = "BASKET_SIMULATION"
    PAPER_LEDGER = "PAPER_LEDGER"
    BACKTEST_EQUITY_CURVE = "BACKTEST_EQUITY_CURVE"
    CUSTOM_RETURNS = "CUSTOM_RETURNS"
    MOCK = "MOCK"


class StressScenarioType(str, Enum):
    MARKET_SHOCK = "MARKET_SHOCK"
    SECTOR_SHOCK = "SECTOR_SHOCK"
    VOLATILITY_SPIKE = "VOLATILITY_SPIKE"
    CORRELATION_SPIKE = "CORRELATION_SPIKE"
    LIQUIDITY_STRESS = "LIQUIDITY_STRESS"
    GAP_DOWN = "GAP_DOWN"
    LOSING_STREAK = "LOSING_STREAK"
    CUSTOM = "CUSTOM"


class StressStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class MonteCarloMethod(str, Enum):
    BOOTSTRAP = "BOOTSTRAP"
    BLOCK_BOOTSTRAP = "BLOCK_BOOTSTRAP"
    NORMAL_PARAMETRIC = "NORMAL_PARAMETRIC"
    HISTORICAL_SHUFFLE = "HISTORICAL_SHUFFLE"


class StressSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class ReturnSeries(BaseModel):
    series_id: str = Field(..., description="Unique identifier for the return series")
    symbol: str | None = Field(None, description="Optional symbol if specific to one asset")
    source_type: StressInputType = Field(..., description="The source of the returns data")
    returns: list[float] = Field(default_factory=list, description="List of periodic returns")
    start_date: datetime | None = Field(None, description="Start date of the returns data")
    end_date: datetime | None = Field(None, description="End date of the returns data")
    frequency: str = Field(..., description="Frequency of the returns, e.g. daily, weekly")
    warnings: list[str] = Field(
        default_factory=list, description="Warnings generated during series creation"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extra metadata")

    @model_validator(mode="after")
    def validate_series(self) -> "ReturnSeries":
        if not self.returns:
            self.warnings.append("Return series is empty.")

        cleaned = [r for r in self.returns if r == r and r not in (float("inf"), float("-inf"))]
        if len(cleaned) != len(self.returns):
            self.warnings.append(
                f"Cleaned {len(self.returns) - len(cleaned)} invalid returns (NaN/inf)."
            )
        self.returns = cleaned

        if not self.frequency:
            raise ValueError("frequency is required.")
        return self


class StressScenario(BaseModel):
    scenario_id: str
    name: str
    scenario_type: StressScenarioType
    severity: StressSeverity
    market_shock_pct: float | None = None
    volatility_multiplier: float | None = None
    correlation_multiplier: float | None = None
    sector_shocks: dict[str, float] = Field(default_factory=dict)
    symbol_shocks: dict[str, float] = Field(default_factory=dict)
    losing_streak_days: int | None = None
    liquidity_haircut_pct: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MonteCarloConfig(BaseModel):
    method: MonteCarloMethod
    simulations: int
    horizon_days: int
    seed: int
    block_size: int | None = None
    initial_value: float
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_config(self) -> "MonteCarloConfig":
        if self.simulations <= 0:
            raise ValueError("simulations must be positive")
        if self.horizon_days <= 0:
            raise ValueError("horizon_days must be positive")
        if self.initial_value <= 0:
            raise ValueError("initial_value must be positive")
        if self.block_size is not None and self.block_size <= 0:
            raise ValueError("block_size must be positive if provided")
        return self


class MonteCarloResult(BaseModel):
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config: MonteCarloConfig
    status: StressStatus
    final_values: list[float] = Field(default_factory=list)
    final_return_pct_p05: float | None = None
    final_return_pct_p50: float | None = None
    final_return_pct_p95: float | None = None
    max_drawdown_pct_p05: float | None = None
    max_drawdown_pct_p50: float | None = None
    max_drawdown_pct_p95: float | None = None
    ruin_probability_pct: float | None = None
    sample_paths: list[list[float]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Monte Carlo result is research-only. Past results do not guarantee future performance. No real order was sent."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class ShockScenarioResult(BaseModel):
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario: StressScenario
    status: StressStatus
    estimated_portfolio_impact_pct: float | None = None
    estimated_value_after_shock: float | None = None
    item_impacts: dict[str, float] = Field(default_factory=dict)
    exposure_impacts: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Shock scenario is hypothetical research-only. Not investment advice. No real order was sent."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class DrawdownSimulationResult(BaseModel):
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: StressStatus
    max_drawdown_pct: float | None = None
    average_drawdown_pct: float | None = None
    longest_drawdown_days: int | None = None
    recovery_days_estimate: int | None = None
    underwater_curve: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Drawdown simulation is hypothetical research-only. Not investment advice. No real order was sent."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class RiskOfRuinResult(BaseModel):
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: StressStatus
    ruin_threshold_pct: float
    estimated_ruin_probability_pct: float | None = None
    expected_loss_streak: int | None = None
    worst_loss_streak: int | None = None
    required_buffer_estimate_pct: float | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Risk-of-ruin output is a research estimate only. It is not a certainty. No real order was sent."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class StressTestRequest(BaseModel):
    input_type: StressInputType
    snapshot_id: str | None = None
    symbols: list[str] = Field(default_factory=list)
    source: str = "local"
    timeframe: str = "1D"
    scenarios: list[StressScenario] = Field(default_factory=list)
    monte_carlo_config: MonteCarloConfig
    ruin_threshold_pct: float
    include_monte_carlo: bool = True
    include_shock_scenarios: bool = True
    include_drawdown: bool = True
    include_risk_of_ruin: bool = True
    save_output: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_request(self) -> "StressTestRequest":
        valid_sources = {"local", "mock", "local_file", "cache"}
        if self.source not in valid_sources:
            raise ValueError(f"Source must be one of {valid_sources}")
        if not (0 <= self.ruin_threshold_pct <= 100):
            raise ValueError("ruin_threshold_pct must be between 0 and 100")
        self.symbols = [s.strip().upper() for s in self.symbols if s.strip()]
        return self


class StressTestResult(BaseModel):
    stress_id: str
    request: StressTestRequest
    status: StressStatus
    input_summary: dict[str, Any] = Field(default_factory=dict)
    monte_carlo_result: MonteCarloResult | None = None
    shock_results: list[ShockScenarioResult] = Field(default_factory=list)
    drawdown_result: DrawdownSimulationResult | None = None
    risk_of_ruin_result: RiskOfRuinResult | None = None
    stress_score: float | None = None
    stress_rating: StressSeverity
    output_files: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "Stress test result is research-only. Not investment advice. No real order was sent."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "stress_id": self.stress_id,
            "status": self.status.value,
            "stress_score": self.stress_score,
            "stress_rating": self.stress_rating.value,
            "warnings_count": len(self.warnings),
            "mc_p05_return_pct": (
                self.monte_carlo_result.final_return_pct_p05 if self.monte_carlo_result else None
            ),
            "ruin_prob_pct": (
                self.risk_of_ruin_result.estimated_ruin_probability_pct
                if self.risk_of_ruin_result
                else None
            ),
            "max_drawdown_pct": (
                self.drawdown_result.max_drawdown_pct if self.drawdown_result else None
            ),
            "shock_count": len(self.shock_results),
        }

    def safe_public_dict(self) -> dict[str, Any]:
        return {
            "stress_id": self.stress_id,
            "status": self.status.value,
            "stress_rating": self.stress_rating.value,
            "disclaimer": self.disclaimer,
            "summary": self.summary(),
        }
