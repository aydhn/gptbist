from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, List, Dict
import pandas as pd

from bist_signal_bot.costs.models import CostScenario, OrderSide
from bist_signal_bot.signals.models import SignalDirection

class BacktestMode(str, Enum):
    SINGLE_SYMBOL = "SINGLE_SYMBOL"
    MULTI_SYMBOL = "MULTI_SYMBOL"
    PORTFOLIO = "PORTFOLIO"

class ExecutionPriceMode(str, Enum):
    NEXT_OPEN = "NEXT_OPEN"
    NEXT_CLOSE = "NEXT_CLOSE"
    SAME_CLOSE_FOR_RESEARCH_ONLY = "SAME_CLOSE_FOR_RESEARCH_ONLY"

class PositionState(str, Enum):
    FLAT = "FLAT"
    LONG = "LONG"
    SHORT = "SHORT"

class BacktestOrderType(str, Enum):
    MARKET = "MARKET"
    CLOSE_POSITION = "CLOSE_POSITION"

@dataclass
class BacktestOrder:
    symbol: str
    side: OrderSide
    order_type: BacktestOrderType
    quantity: float
    requested_price: float | None
    requested_at: datetime
    reason: str
    execute_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class SimulatedTrade:
    gross_entry_price: float | None = None
    simulated_entry_fill_price: float | None = None
    gross_exit_price: float | None = None
    simulated_exit_fill_price: float | None = None
    total_cost: float = 0.0
    gross_pnl: float | None = None
    net_pnl: float | None = None

class BacktestFill:
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    effective_price: float
    gross_notional: float
    filled_at: datetime
    order_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class BacktestConfig:
    include_transaction_costs: bool = True
    include_slippage: bool = True
    execution_scenario: str = "BASE"
    simulated_order_type: str = "NEXT_CLOSE"

class BacktestTrade:
    symbol: str
    entry_time: datetime
    side: SignalDirection
    quantity: float
    entry_price: float
    entry_cost: float
    exit_time: datetime | None = None
    exit_price: float | None = None
    exit_cost: float = 0.0
    return_pct: float | None = None
    bars_held: int | None = None
    entry_reason: str | None = None
    exit_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_closed(self) -> bool:
        return self.exit_time is not None

@dataclass
class PortfolioSnapshot:
    timestamp: datetime
    cash: float
    position_value: float
    equity: float
    gross_exposure: float
    net_exposure: float
    open_positions: int
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class BacktestConfig:
    initial_capital: float
    execution_price_mode: ExecutionPriceMode
    commission_enabled: bool
    slippage_enabled: bool
    allow_short: bool
    max_position_size_pct: float
    min_trade_notional: float
    trade_on_candidate_statuses: list[str]
    close_on_opposite_signal: bool
    close_on_flat_signal: bool
    one_position_per_symbol: bool
    use_fractional_shares: bool
    close_open_positions_at_end: bool
    scenario: CostScenario
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.initial_capital <= 0:
            from bist_signal_bot.core.exceptions import BacktestValidationError
            raise BacktestValidationError("initial_capital must be > 0")
        if not (0.0 <= self.max_position_size_pct <= 1.0):
            from bist_signal_bot.core.exceptions import BacktestValidationError
            raise BacktestValidationError("max_position_size_pct must be between 0.0 and 1.0")
        if self.min_trade_notional < 0:
            from bist_signal_bot.core.exceptions import BacktestValidationError
            raise BacktestValidationError("min_trade_notional must be >= 0")

@dataclass
class BacktestResult:
    strategy_name: str
    mode: BacktestMode
    config: BacktestConfig
    trades: list[BacktestTrade]
    fills: list[BacktestFill]
    portfolio_snapshots: list[PortfolioSnapshot]
    orders: list[BacktestOrder]
    started_at: datetime
    finished_at: datetime
    elapsed_seconds: float
    data_source: Optional[str] = None
    data_lineage_checksum: Optional[str] = None
    data_row_count: Optional[int] = None
    data_import_timestamp: Optional[datetime] = None
    issues: list[str] = field(default_factory=list)
    symbol: str | None = None
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)
    metadata: dict[str, Any] = field(default_factory=dict)
    breadth_regime_subset_metrics: dict[str, Any] = field(default_factory=dict)
    disclaimer: str = "Backtest research output only. Past performance does not guarantee future results. Not investment advice. No order was sent."

    def trade_count(self) -> int:
        return len(self.trades)

    def closed_trade_count(self) -> int:
        return sum(1 for t in self.trades if t.is_closed())

    def final_equity(self) -> float:
        if not self.portfolio_snapshots:
            return self.config.initial_capital
        return self.portfolio_snapshots[-1].equity

    def total_return_pct(self) -> float:
        initial = self.config.initial_capital
        if initial == 0:
            return 0.0
        return ((self.final_equity() - initial) / initial) * 100.0

    def total_cost(self) -> float:
        return sum(f.total_cost for f in self.fills)

    def summary(self) -> dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "initial_capital": self.config.initial_capital,
            "final_equity": self.final_equity(),
            "total_return_pct": self.total_return_pct(),
            "trade_count": self.trade_count(),
            "closed_trade_count": self.closed_trade_count(),
            "total_cost": self.total_cost(),
            "execution_mode": self.config.execution_price_mode.value,
            "cost_scenario": self.config.scenario.value,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "disclaimer": self.disclaimer,
        }

@dataclass
class BenchmarkComparisonReport:
    strategy_name: str
    benchmark_name: str
    symbol: str | None
    strategy_total_return_pct: float
    benchmark_total_return_pct: float
    excess_return_pct: float
    strategy_max_drawdown_pct: float | None
    benchmark_max_drawdown_pct: float | None
    strategy_sharpe: float | None
    benchmark_sharpe: float | None
    outperform: bool | None
    warnings: list[str]
    generated_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return self.__dict__

@dataclass
class ReturnMetrics:
    total_return_pct: float
    annualized_return_pct: float | None
    cumulative_return_pct: float
    average_daily_return_pct: float | None
    best_day_return_pct: float | None
    worst_day_return_pct: float | None

@dataclass
class RiskMetrics:
    volatility_annualized_pct: float | None
    downside_volatility_pct: float | None
    max_drawdown_pct: float | None
    max_drawdown_duration_bars: int | None
    value_at_risk_95_pct: float | None
    conditional_value_at_risk_95_pct: float | None

@dataclass
class RiskAdjustedMetrics:
    sharpe_ratio: float | None
    sortino_ratio: float | None
    calmar_ratio: float | None
    return_over_max_drawdown: float | None

@dataclass
class TradeMetrics:
    trade_count: int
    closed_trade_count: int
    winning_trades: int
    losing_trades: int
    breakeven_trades: int
    win_rate_pct: float | None
    loss_rate_pct: float | None
    average_trade_return_pct: float | None
    average_winner_pct: float | None
    average_loser_pct: float | None
    best_trade_pct: float | None
    worst_trade_pct: float | None
    gross_profit: float
    gross_loss: float
    net_profit: float
    profit_factor: float | None
    expectancy: float | None
    average_bars_held: float | None

@dataclass
class CostMetrics:
    total_commission: float
    total_slippage: float
    total_spread: float
    total_tax: float
    total_other_fees: float
    cost_as_pct_of_initial_capital: float | None
    cost_as_pct_of_gross_profit: float | None

@dataclass
class ExposureMetrics:
    average_exposure_pct: float | None
    max_exposure_pct: float | None
    time_in_market_pct: float | None
    average_open_positions: float | None
    max_open_positions: int | None

@dataclass
class BacktestPerformanceReport:
    strategy_name: str
    symbol: str | None
    timeframe: str
    initial_capital: float
    final_equity: float
    return_metrics: ReturnMetrics
    risk_metrics: RiskMetrics
    risk_adjusted_metrics: RiskAdjustedMetrics
    trade_metrics: TradeMetrics
    cost_metrics: CostMetrics
    exposure_metrics: ExposureMetrics
    started_at: datetime
    finished_at: datetime
    generated_at: datetime
    warnings: list[str]
    disclaimer: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "initial_capital": self.initial_capital,
            "final_equity": self.final_equity,
            "returns": self.return_metrics.__dict__,
            "risk": self.risk_metrics.__dict__,
            "risk_adjusted": self.risk_adjusted_metrics.__dict__,
            "trades": self.trade_metrics.__dict__,
            "costs": self.cost_metrics.__dict__,
            "exposure": self.exposure_metrics.__dict__,
            "warnings": self.warnings,
            "disclaimer": self.disclaimer
        }

    def compact_summary(self) -> dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "initial_capital": self.initial_capital,
            "final_equity": self.final_equity,
            "total_return_pct": self.return_metrics.total_return_pct,
            "annualized_return_pct": self.return_metrics.annualized_return_pct,
            "max_drawdown_pct": self.risk_metrics.max_drawdown_pct,
            "sharpe_ratio": self.risk_adjusted_metrics.sharpe_ratio,
            "win_rate_pct": self.trade_metrics.win_rate_pct,
            "profit_factor": self.trade_metrics.profit_factor,
            "trade_count": self.trade_metrics.trade_count,
            "total_cost": self.cost_metrics.total_cost
        }

@dataclass
class BenchmarkComparisonReport:
    strategy_name: str
    benchmark_name: str
    symbol: str | None
    strategy_total_return_pct: float
    benchmark_total_return_pct: float
    excess_return_pct: float
    strategy_max_drawdown_pct: float | None
    benchmark_max_drawdown_pct: float | None
    strategy_sharpe: float | None
    benchmark_sharpe: float | None
    outperform: bool | None
    warnings: list[str]
    generated_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return self.__dict__

@dataclass
class BacktestReportBundle:
    backtest_result: BacktestResult
    performance_report: BacktestPerformanceReport
    benchmark_comparisons: list[BenchmarkComparisonReport]
    equity_curve: pd.DataFrame
    drawdown_curve: pd.DataFrame
    trades: pd.DataFrame
    generated_at: datetime
    output_files: dict[str, str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "performance_report": self.performance_report.compact_summary(),
            "benchmark_comparisons": [b.summary() for b in self.benchmark_comparisons],
            "output_files": self.output_files,
            "generated_at": self.generated_at.isoformat()
        }
    gross_return_pct: float | None = None
    net_return_pct: float | None = None
    total_transaction_cost: float = 0.0
    average_slippage_bps: float | None = None
    fill_rate_pct: float | None = None
    execution_quality_report_id: str | None = None

    # --- Phase 70 Execution Sim Additions ---
    # In a real environment we'd carefully add these directly inside the dataclass block
    # For now we assume these properties are accessible or patched in at runtime
