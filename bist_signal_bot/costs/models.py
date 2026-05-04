from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from bist_signal_bot.core.exceptions import CostModelError


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    UNKNOWN = "UNKNOWN"


class LiquidityBucket(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class CostScenario(str, Enum):
    OPTIMISTIC = "OPTIMISTIC"
    BASE = "BASE"
    CONSERVATIVE = "CONSERVATIVE"
    STRESS = "STRESS"


class SlippageModelType(str, Enum):
    FIXED_BPS = "FIXED_BPS"
    VOLUME_BASED = "VOLUME_BASED"
    VOLATILITY_BASED = "VOLATILITY_BASED"
    HYBRID = "HYBRID"


class CommissionModelType(str, Enum):
    BPS = "BPS"
    FLAT = "FLAT"
    BPS_PLUS_FLAT = "BPS_PLUS_FLAT"


class SpreadModelType(str, Enum):
    FIXED_BPS = "FIXED_BPS"
    LIQUIDITY_BUCKET = "LIQUIDITY_BUCKET"
    VOLUME_BASED = "VOLUME_BASED"


@dataclass
class TradeCostInput:
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float
    notional: float | None = None
    average_daily_volume: float | None = None
    average_daily_turnover: float | None = None
    volatility: float | None = None
    liquidity_bucket: LiquidityBucket = LiquidityBucket.UNKNOWN
    timestamp: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.symbol = self.symbol.upper().strip()

        if self.quantity <= 0:
            raise CostModelError(f"Quantity must be > 0. Got: {self.quantity}")
        if self.price <= 0:
            raise CostModelError(f"Price must be > 0. Got: {self.price}")

        if self.notional is not None:
            if self.notional <= 0:
                raise CostModelError(f"Notional must be > 0. Got: {self.notional}")

        if self.average_daily_volume is not None and self.average_daily_volume < 0:
             raise CostModelError(f"Average daily volume cannot be negative. Got: {self.average_daily_volume}")

        if self.average_daily_turnover is not None and self.average_daily_turnover < 0:
             raise CostModelError(f"Average daily turnover cannot be negative. Got: {self.average_daily_turnover}")

        if self.volatility is not None and self.volatility < 0:
             raise CostModelError(f"Volatility cannot be negative. Got: {self.volatility}")

    def computed_notional(self) -> float:
        if self.notional is not None:
            return self.notional
        return self.quantity * self.price


@dataclass
class CommissionResult:
    commission_amount: float
    commission_rate_bps: float
    flat_fee: float
    min_commission_applied: bool
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SlippageResult:
    slippage_bps: float
    slippage_amount_per_share: float
    slippage_total_amount: float
    adjusted_price: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SpreadResult:
    spread_bps: float
    spread_amount_per_share: float
    spread_total_amount: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TransactionCostBreakdown:
    input: TradeCostInput
    commission: CommissionResult
    slippage: SlippageResult
    spread: SpreadResult
    tax_amount: float
    other_fees: float
    gross_notional: float
    total_cost: float
    total_cost_bps: float
    effective_price: float
    side: OrderSide
    scenario: CostScenario
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def summary(self) -> dict[str, Any]:
        return {
            "symbol": self.input.symbol,
            "side": self.side.value,
            "quantity": self.input.quantity,
            "price": self.input.price,
            "gross_notional": self.gross_notional,
            "total_cost": self.total_cost,
            "total_cost_bps": self.total_cost_bps,
            "effective_price": self.effective_price,
            "commission_amount": self.commission.commission_amount,
            "slippage_bps": self.slippage.slippage_bps,
            "slippage_amount": self.slippage.slippage_total_amount,
            "spread_bps": self.spread.spread_bps,
            "spread_amount": self.spread.spread_total_amount,
            "tax_amount": self.tax_amount,
            "other_fees": self.other_fees,
            "scenario": self.scenario.value
        }

    def cost_as_pct_of_notional(self) -> float:
        if self.gross_notional == 0:
            return 0.0
        return (self.total_cost / self.gross_notional) * 100


@dataclass
class RoundTripCostBreakdown:
    entry_cost: TransactionCostBreakdown
    exit_cost: TransactionCostBreakdown
    total_cost: float
    total_cost_bps: float
    breakeven_move_pct: float
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def summary(self) -> dict[str, Any]:
        return {
            "symbol": self.entry_cost.input.symbol,
            "quantity": self.entry_cost.input.quantity,
            "entry_side": self.entry_cost.side.value,
            "exit_side": self.exit_cost.side.value,
            "entry_price": self.entry_cost.input.price,
            "exit_price": self.exit_cost.input.price,
            "entry_effective_price": self.entry_cost.effective_price,
            "exit_effective_price": self.exit_cost.effective_price,
            "total_round_trip_cost": self.total_cost,
            "total_round_trip_cost_bps": self.total_cost_bps,
            "breakeven_move_pct": self.breakeven_move_pct,
            "scenario": self.entry_cost.scenario.value
        }
