from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
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
class BacktestFill:
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    effective_price: float
    gross_notional: float
    total_cost: float
    total_cost_bps: float
    filled_at: datetime
    order_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
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
    gross_pnl: float | None = None
    net_pnl: float | None = None
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
    issues: list[str]
    symbol: str | None = None
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)
    metadata: dict[str, Any] = field(default_factory=dict)
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
