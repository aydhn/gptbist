import json
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any

from bist_signal_bot.core.exceptions import MonteCarloValidationError

class MonteCarloStatus(Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class ResamplingMethod(Enum):
    TRADE_BOOTSTRAP = "TRADE_BOOTSTRAP"
    TRADE_SHUFFLE = "TRADE_SHUFFLE"
    RETURN_BOOTSTRAP = "RETURN_BOOTSTRAP"
    BLOCK_BOOTSTRAP = "BLOCK_BOOTSTRAP"
    STATIONARY_BOOTSTRAP = "STATIONARY_BOOTSTRAP"
    PARAMETRIC_NORMAL = "PARAMETRIC_NORMAL"
    EMPIRICAL_PATH = "EMPIRICAL_PATH"
    CUSTOM = "CUSTOM"

class MonteCarloTarget(Enum):
    TRADES = "TRADES"
    RETURNS = "RETURNS"
    EQUITY_CURVE = "EQUITY_CURVE"
    BACKTEST_RESULT = "BACKTEST_RESULT"
    PORTFOLIO_BASKET = "PORTFOLIO_BASKET"
    VALIDATION_FOLDS = "VALIDATION_FOLDS"
    CUSTOM = "CUSTOM"

class MonteCarloMetricType(Enum):
    FINAL_EQUITY = "FINAL_EQUITY"
    TOTAL_RETURN = "TOTAL_RETURN"
    NET_TOTAL_RETURN = "NET_TOTAL_RETURN"
    MAX_DRAWDOWN = "MAX_DRAWDOWN"
    SHARPE = "SHARPE"
    SORTINO = "SORTINO"
    WIN_RATE = "WIN_RATE"
    PROFIT_FACTOR = "PROFIT_FACTOR"
    LOSS_STREAK = "LOSS_STREAK"
    RUIN_PROBABILITY = "RUIN_PROBABILITY"
    COST_DRAG = "COST_DRAG"
    SLIPPAGE_BPS = "SLIPPAGE_BPS"
    FILL_RATE = "FILL_RATE"
    TAIL_LOSS = "TAIL_LOSS"
    VAR = "VAR"
    CVAR = "CVAR"
    CUSTOM = "CUSTOM"

class RealityCheckStatus(Enum):
    ROBUST = "ROBUST"
    WATCH = "WATCH"
    LIKELY_OVERFIT = "LIKELY_OVERFIT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class MonteCarloSeverity(Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class MonteCarloRequest:
    request_id: str
    target: MonteCarloTarget
    method: ResamplingMethod
    simulations: int
    seed: int
    initial_equity: float
    ruin_threshold_pct: float
    strategy_name: str | None = None
    symbol: str | None = None
    block_size: int | None = None
    include_cost_randomization: bool = False
    include_slippage_randomization: bool = False
    include_reality_check: bool = False
    save_output: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.simulations <= 0:
            raise MonteCarloValidationError("Simulations must be positive.")
        if self.initial_equity <= 0:
            raise MonteCarloValidationError("Initial equity must be positive.")
        if not (0 <= self.ruin_threshold_pct <= 100):
            raise MonteCarloValidationError("Ruin threshold must be between 0 and 100.")
        if self.block_size is not None and self.block_size <= 0:
            raise MonteCarloValidationError("Block size must be positive.")
        if not isinstance(self.seed, int):
            raise MonteCarloValidationError("Seed must be an integer.")
        if self.symbol:
            self.symbol = self.symbol.upper()

@dataclass
class MonteCarloPath:
    path_id: str
    simulation_index: int
    equity_curve: list[float]
    returns: list[float]
    trades_count: int
    final_equity: float
    total_return_pct: float
    max_drawdown_pct: float
    ruin_hit: bool
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class MonteCarloMetric:
    metric_id: str
    metric_type: MonteCarloMetricType
    name: str
    status: MonteCarloStatus
    mean: float | None = None
    median: float | None = None
    std: float | None = None
    p05: float | None = None
    p25: float | None = None
    p75: float | None = None
    p95: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    observed_value: float | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class MonteCarloDistribution:
    distribution_id: str
    metric_type: MonteCarloMetricType
    values: list[float]
    percentiles: dict[str, float]
    observations_count: int
    observed_value: float | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class CostRandomizationConfig:
    config_id: str
    commission_multiplier_min: float
    commission_multiplier_max: float
    slippage_multiplier_min: float
    slippage_multiplier_max: float
    spread_multiplier_min: float
    spread_multiplier_max: float
    market_impact_multiplier_min: float
    market_impact_multiplier_max: float
    deterministic_seed: int
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        multipliers = [
            self.commission_multiplier_min, self.commission_multiplier_max,
            self.slippage_multiplier_min, self.slippage_multiplier_max,
            self.spread_multiplier_min, self.spread_multiplier_max,
            self.market_impact_multiplier_min, self.market_impact_multiplier_max
        ]
        if any(m < 0 for m in multipliers):
            raise MonteCarloValidationError("Multipliers cannot be negative.")
        if self.commission_multiplier_min > self.commission_multiplier_max:
            raise MonteCarloValidationError("Commission min > max.")
        if self.slippage_multiplier_min > self.slippage_multiplier_max:
            raise MonteCarloValidationError("Slippage min > max.")
        if self.spread_multiplier_min > self.spread_multiplier_max:
            raise MonteCarloValidationError("Spread min > max.")
        if self.market_impact_multiplier_min > self.market_impact_multiplier_max:
            raise MonteCarloValidationError("Market impact min > max.")

@dataclass
class RealityCheckResult:
    reality_check_id: str
    status: RealityCheckStatus
    observed_metric: str
    trials_count: int
    strategy_name: str | None = None
    symbol: str | None = None
    observed_value: float | None = None
    simulated_p_value: float | None = None
    percentile_rank: float | None = None
    multiple_testing_warning: bool = False
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Reality check is research-only. It does not prove future performance. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class MonteCarloRiskSummary:
    summary_id: str
    ruin_probability_pct: float | None = None
    probability_negative_return_pct: float | None = None
    probability_drawdown_above_threshold_pct: float | None = None
    expected_tail_loss_pct: float | None = None
    cvar_5_pct: float | None = None
    median_final_equity: float | None = None
    p05_final_equity: float | None = None
    p95_final_equity: float | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class MonteCarloResult:
    monte_carlo_id: str
    request: MonteCarloRequest
    status: MonteCarloStatus
    elapsed_seconds: float
    paths: list[MonteCarloPath]
    metrics: list[MonteCarloMetric]
    distributions: list[MonteCarloDistribution]
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    risk_summary: MonteCarloRiskSummary | None = None
    reality_check: RealityCheckResult | None = None
    robustness_score: float | None = None
    recommended_actions: list[str] = field(default_factory=list)
    output_files: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    disclaimer: str = "Monte Carlo result is research-only. Simulated outcomes do not guarantee future performance. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "monte_carlo_id": self.monte_carlo_id,
            "status": self.status.value,
            "robustness_score": self.robustness_score,
            "ruin_probability_pct": self.risk_summary.ruin_probability_pct if self.risk_summary else None,
            "reality_check_status": self.reality_check.status.value if self.reality_check else None,
            "warnings_count": len(self.warnings),
            "errors_count": len(self.errors)
        }

    def safe_public_dict(self) -> dict[str, Any]:
        res = self.summary()
        res["strategy"] = self.request.strategy_name
        res["symbol"] = self.request.symbol
        res["disclaimer"] = self.disclaimer
        if self.risk_summary:
            res["cvar_5_pct"] = self.risk_summary.cvar_5_pct
            res["p05_final_equity"] = self.risk_summary.p05_final_equity
        return res
