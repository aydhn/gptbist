from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any, Optional

from bist_signal_bot.strategies.models import SignalCandidate
from bist_signal_bot.risk.models import RiskDecision
from bist_signal_bot.portfolio.models import PortfolioRiskDecision

class PaperAccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"
    ERROR = "ERROR"

class PaperOrderStatus(str, Enum):
    CREATED = "CREATED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    ERROR = "ERROR"

class PaperOrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class PaperOrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    CLOSE_POSITION = "CLOSE_POSITION"

class PaperExecutionMode(str, Enum):
    LATEST_CLOSE_RESEARCH = "LATEST_CLOSE_RESEARCH"
    NEXT_OPEN_SIMULATED = "NEXT_OPEN_SIMULATED"
    NEXT_CLOSE_SIMULATED = "NEXT_CLOSE_SIMULATED"
    MANUAL_PRICE = "MANUAL_PRICE"

class PaperPositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"

class PaperLedgerEventType(str, Enum):
    ACCOUNT_INITIALIZED = "ACCOUNT_INITIALIZED"
    ACCOUNT_RESET = "ACCOUNT_RESET"
    ORDER_CREATED = "ORDER_CREATED"
    ORDER_ACCEPTED = "ORDER_ACCEPTED"
    ORDER_REJECTED = "ORDER_REJECTED"
    ORDER_FILLED = "ORDER_FILLED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    POSITION_OPENED = "POSITION_OPENED"
    POSITION_CLOSED = "POSITION_CLOSED"
    CASH_UPDATED = "CASH_UPDATED"
    MARK_TO_MARKET = "MARK_TO_MARKET"
    RISK_DECISION_ATTACHED = "RISK_DECISION_ATTACHED"
    PORTFOLIO_DECISION_ATTACHED = "PORTFOLIO_DECISION_ATTACHED"
    UNKNOWN = "UNKNOWN"

class PaperAccount(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    account_id: str
    status: PaperAccountStatus = PaperAccountStatus.ACTIVE
    initial_cash: float
    cash: float
    equity: float
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    total_costs: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("account_id")
    def id_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("account_id boş olamaz.")
        return v

    @field_validator("initial_cash")
    def initial_cash_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("initial_cash > 0 olmalı")
        return v

    @field_validator("cash", "equity", "total_costs")
    def values_must_not_be_negative(cls, v):
        if v < 0:
            raise ValueError("cash, equity, total_costs negatif olamaz.")
        return v

class PaperOrder(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    order_id: str
    account_id: str
    symbol: str
    side: PaperOrderSide
    order_type: PaperOrderType
    status: PaperOrderStatus
    quantity: float
    requested_price: Optional[float] = None
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    signal_id: Optional[str] = None
    strategy_name: Optional[str] = None
    risk_decision_summary: dict[str, Any] = Field(default_factory=dict)
    portfolio_decision_summary: dict[str, Any] = Field(default_factory=dict)
    reject_reason: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("order_id", "account_id")
    def id_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("ID boş olamaz.")
        return v

    @field_validator("symbol")
    def normalize_symbol(cls, v):
        return v.upper()

    @field_validator("quantity")
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("quantity > 0 olmalı")
        return v

    @model_validator(mode='after')
    def prices_must_be_positive(self):
        for price_attr in ["requested_price", "limit_price", "stop_price"]:
            price = getattr(self, price_attr)
            if price is not None and price <= 0:
                raise ValueError(f"{price_attr} > 0 olmalı")
        return self

class PaperFill(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    fill_id: str
    order_id: str
    account_id: str
    symbol: str
    side: PaperOrderSide
    quantity: float
    requested_price: Optional[float] = None
    fill_price: float
    effective_price: float
    gross_notional: float
    commission: float = 0.0
    slippage: float = 0.0
    spread: float = 0.0
    tax: float = 0.0
    other_fees: float = 0.0
    total_cost: float = 0.0
    filled_at: datetime = Field(default_factory=datetime.utcnow)
    execution_mode: PaperExecutionMode
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("quantity", "fill_price", "effective_price")
    def must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Değer > 0 olmalı")
        return v

    @field_validator("commission", "slippage", "spread", "tax", "other_fees", "total_cost")
    def costs_must_not_be_negative(cls, v):
        if v < 0:
            raise ValueError("costs negatif olamaz.")
        return v

class PaperPosition(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    position_id: str
    account_id: str
    symbol: str
    side: PaperPositionSide
    quantity: float
    avg_entry_price: float
    last_price: float
    market_value: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    opened_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None
    is_open: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("quantity")
    def qty_must_not_be_negative(cls, v):
        if v < 0:
            raise ValueError("quantity >= 0 olmalı")
        return v

    @field_validator("avg_entry_price", "last_price")
    def prices_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Fiyatlar > 0 olmalı")
        return v

    @field_validator("market_value")
    def market_value_must_not_be_negative(cls, v):
        if v < 0:
            raise ValueError("market_value >= 0 olmalı")
        return v

class PaperTrade(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    trade_id: str
    account_id: str
    symbol: str
    side: PaperPositionSide
    entry_fill_id: str
    exit_fill_id: Optional[str] = None
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    entry_time: datetime
    exit_time: Optional[datetime] = None
    gross_pnl: Optional[float] = None
    net_pnl: Optional[float] = None
    total_cost: float
    return_pct: Optional[float] = None
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class PaperLedgerEvent(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    event_id: str
    account_id: str
    event_type: PaperLedgerEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    symbol: Optional[str] = None
    order_id: Optional[str] = None
    fill_id: Optional[str] = None
    position_id: Optional[str] = None
    trade_id: Optional[str] = None
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class PaperLedgerState(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    account: PaperAccount
    orders: list[PaperOrder] = Field(default_factory=list)
    fills: list[PaperFill] = Field(default_factory=list)
    positions: list[PaperPosition] = Field(default_factory=list)
    trades: list[PaperTrade] = Field(default_factory=list)
    events: list[PaperLedgerEvent] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    schema_version: str = "1.0"

    def open_positions(self) -> list[PaperPosition]:
        return [p for p in self.positions if p.is_open]

    def open_position_symbols(self) -> list[str]:
        return [p.symbol for p in self.open_positions()]

    def orders_by_status(self, status: PaperOrderStatus) -> list[PaperOrder]:
        return [o for o in self.orders if o.status == status]

    def summary(self) -> dict[str, Any]:
        return {
            "account_id": self.account.account_id,
            "status": self.account.status.value,
            "cash": self.account.cash,
            "equity": self.account.equity,
            "open_positions": len(self.open_positions()),
            "total_orders": len(self.orders),
            "total_fills": len(self.fills),
            "total_trades": len(self.trades)
        }

class PaperRunRequest(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    account_id: str
    symbols: list[str]
    strategy_name: str
    source: str
    timeframe: str
    execution_mode: PaperExecutionMode = PaperExecutionMode.LATEST_CLOSE_RESEARCH
    use_trade_risk: bool = True
    use_portfolio_risk: bool = True
    params: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

class PaperRunResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    account: PaperAccount
    signals: list[SignalCandidate] = Field(default_factory=list)
    risk_decisions: list[RiskDecision] = Field(default_factory=list)
    portfolio_decision: Optional[PortfolioRiskDecision] = None
    orders: list[PaperOrder] = Field(default_factory=list)
    fills: list[PaperFill] = Field(default_factory=list)
    positions: list[PaperPosition] = Field(default_factory=list)
    events: list[PaperLedgerEvent] = Field(default_factory=list)
    status: str
    issues: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    elapsed_seconds: float = 0.0
    disclaimer: str = "Paper trading simulation output only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "account_id": self.account.account_id,
            "signals_count": len(self.signals),
            "risk_decisions_count": len(self.risk_decisions),
            "orders_count": len(self.orders),
            "fills_count": len(self.fills),
            "cash": self.account.cash,
            "equity": self.account.equity,
            "status": self.status,
            "issues_count": len(self.issues)
        }


class CreateMarketOrderRequest(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    account_id: str
    symbol: str
    side: PaperOrderSide
    quantity: float
    requested_price: Optional[float] = None
    signal: Optional[SignalCandidate] = None
    risk_decision: Optional[RiskDecision] = None
    portfolio_decision: Optional[PortfolioRiskDecision] = None
