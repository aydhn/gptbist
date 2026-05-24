from enum import Enum
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field

class SimulatedOrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    UNKNOWN = "UNKNOWN"

class SimulatedOrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    NEXT_OPEN = "NEXT_OPEN"
    NEXT_CLOSE = "NEXT_CLOSE"
    VWAP_LIKE = "VWAP_LIKE"
    MID_PRICE = "MID_PRICE"
    CUSTOM = "CUSTOM"

class SimulatedFillStatus(str, Enum):
    FILLED = "FILLED"
    PARTIAL_FILLED = "PARTIAL_FILLED"
    NOT_FILLED = "NOT_FILLED"
    REJECTED_RESEARCH = "REJECTED_RESEARCH"
    SKIPPED_LIQUIDITY = "SKIPPED_LIQUIDITY"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class CostComponentType(str, Enum):
    COMMISSION = "COMMISSION"
    TAX_PLACEHOLDER = "TAX_PLACEHOLDER"
    EXCHANGE_FEE_PLACEHOLDER = "EXCHANGE_FEE_PLACEHOLDER"
    SPREAD_COST = "SPREAD_COST"
    SLIPPAGE_COST = "SLIPPAGE_COST"
    MARKET_IMPACT = "MARKET_IMPACT"
    ROUNDING = "ROUNDING"
    OTHER = "OTHER"

class LiquidityStatus(str, Enum):
    LIQUID = "LIQUID"
    WATCH = "WATCH"
    THIN = "THIN"
    ILLIQUID = "ILLIQUID"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"

class SlippageModelType(str, Enum):
    FIXED_BPS = "FIXED_BPS"
    SPREAD_BASED = "SPREAD_BASED"
    VOLUME_PARTICIPATION = "VOLUME_PARTICIPATION"
    VOLATILITY_ADJUSTED = "VOLATILITY_ADJUSTED"
    HYBRID = "HYBRID"
    CUSTOM = "CUSTOM"

class ExecutionScenarioType(str, Enum):
    OPTIMISTIC = "OPTIMISTIC"
    BASE = "BASE"
    CONSERVATIVE = "CONSERVATIVE"
    STRESS = "STRESS"
    CUSTOM = "CUSTOM"

class TransactionCostConfig(BaseModel):
    config_id: str
    commission_bps: float = Field(ge=0.0)
    min_commission: float = Field(ge=0.0)
    tax_bps_placeholder: float = Field(ge=0.0)
    exchange_fee_bps_placeholder: float = Field(ge=0.0)
    include_spread_cost: bool
    include_slippage_cost: bool
    include_market_impact: bool
    currency: str = "TRY"
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class TransactionCostBreakdown(BaseModel):
    breakdown_id: str
    notional: float
    side: SimulatedOrderSide
    gross_price: float
    quantity: float
    commission: float
    tax_placeholder: float
    exchange_fee_placeholder: float
    spread_cost: float
    slippage_cost: float
    market_impact_cost: float
    rounding_cost: float
    total_cost: float
    total_cost_bps: float | None
    net_notional: float
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Transaction cost breakdown is a configurable research estimate only. It is not broker pricing, tax advice, or investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class SlippageEstimate(BaseModel):
    estimate_id: str
    symbol: str
    model_type: SlippageModelType
    side: SimulatedOrderSide
    reference_price: float
    estimated_slippage_bps: float
    estimated_fill_price: float
    spread_bps: float | None
    participation_rate_pct: float | None
    volatility_pct: float | None
    liquidity_status: LiquidityStatus
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Slippage estimate is hypothetical research-only. It does not guarantee execution price. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class LiquiditySnapshot(BaseModel):
    snapshot_id: str
    symbol: str
    generated_at: datetime
    average_volume: float | None
    average_turnover: float | None
    last_volume: float | None
    last_close: float | None
    median_volume: float | None
    volume_percentile: float | None
    estimated_spread_bps: float | None
    max_research_notional: float | None
    status: LiquidityStatus
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class SimulatedOrder(BaseModel):
    order_id: str
    symbol: str
    side: SimulatedOrderSide
    order_type: SimulatedOrderType
    quantity: float = Field(gt=0.0)
    reference_price: float = Field(gt=0.0)
    limit_price: float | None
    requested_notional: float = Field(gt=0.0)
    signal_id: str | None = None
    strategy_name: str | None = None
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if self.order_type == SimulatedOrderType.LIMIT and self.limit_price is None:
            raise ValueError("LIMIT order requires limit_price")
        self.symbol = self.symbol.upper().strip()

class SimulatedFill(BaseModel):
    fill_id: str
    order_id: str
    symbol: str
    status: SimulatedFillStatus
    filled_quantity: float
    unfilled_quantity: float
    average_fill_price: float | None
    reference_price: float
    gross_notional: float
    net_notional: float
    cost_breakdown: TransactionCostBreakdown | None = None
    slippage_estimate: SlippageEstimate | None = None
    liquidity_snapshot: LiquiditySnapshot | None = None
    fill_probability: float | None = None
    reason: str | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Simulated fill is research-only. It is not a real order or execution report. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ExecutionQualityReport(BaseModel):
    report_id: str
    symbol: str | None
    strategy_name: str | None
    fills: list[SimulatedFill]
    total_orders: int
    filled_orders: int
    partial_orders: int
    not_filled_orders: int
    gross_pnl: float | None
    net_pnl: float | None
    total_cost: float
    average_slippage_bps: float | None
    average_total_cost_bps: float | None
    fill_rate_pct: float | None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Execution quality report is simulated research output only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ExecutionScenario(BaseModel):
    scenario_id: str
    scenario_type: ExecutionScenarioType
    name: str
    cost_multiplier: float
    slippage_multiplier: float
    liquidity_haircut_pct: float
    fill_probability_multiplier: float
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
