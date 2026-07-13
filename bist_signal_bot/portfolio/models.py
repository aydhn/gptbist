from enum import Enum
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd
from datetime import datetime
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, field_validator, model_validator

from bist_signal_bot.signals.models import SignalCandidate
from bist_signal_bot.risk.models import RiskDecision

class PortfolioPositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"

class PortfolioDecisionStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REDUCED = "REDUCED"
    PARTIALLY_APPROVED = "PARTIALLY_APPROVED"
    WATCH_ONLY = "WATCH_ONLY"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class AllocationMethod(str, Enum):
    EQUAL_WEIGHT = "EQUAL_WEIGHT"
    SCORE_WEIGHTED = "SCORE_WEIGHTED"
    RISK_PARITY_SIMPLE = "RISK_PARITY_SIMPLE"
    VOLATILITY_SCALED = "VOLATILITY_SCALED"
    LIQUIDITY_WEIGHTED = "LIQUIDITY_WEIGHTED"
    RISK_BUDGET = "RISK_BUDGET"
    HYBRID = "HYBRID"

class PortfolioRejectReason(str, Enum):
    MAX_POSITIONS_EXCEEDED = "MAX_POSITIONS_EXCEEDED"
    MAX_GROSS_EXPOSURE_EXCEEDED = "MAX_GROSS_EXPOSURE_EXCEEDED"
    MAX_NET_EXPOSURE_EXCEEDED = "MAX_NET_EXPOSURE_EXCEEDED"
    MAX_SYMBOL_WEIGHT_EXCEEDED = "MAX_SYMBOL_WEIGHT_EXCEEDED"
    MAX_SECTOR_WEIGHT_EXCEEDED = "MAX_SECTOR_WEIGHT_EXCEEDED"
    MAX_CORRELATION_EXCEEDED = "MAX_CORRELATION_EXCEEDED"
    MAX_PORTFOLIO_RISK_EXCEEDED = "MAX_PORTFOLIO_RISK_EXCEEDED"
    INSUFFICIENT_CASH = "INSUFFICIENT_CASH"
    DAILY_SIGNAL_LIMIT_EXCEEDED = "DAILY_SIGNAL_LIMIT_EXCEEDED"
    LIQUIDITY_TOO_LOW = "LIQUIDITY_TOO_LOW"
    VOLATILITY_TOO_HIGH = "VOLATILITY_TOO_HIGH"
    DUPLICATE_SYMBOL = "DUPLICATE_SYMBOL"
    SIGNAL_REJECTED_BY_TRADE_RISK = "SIGNAL_REJECTED_BY_TRADE_RISK"
    UNKNOWN = "UNKNOWN"

class PortfolioHolding(BaseModel):
    symbol: str
    side: PortfolioPositionSide
    quantity: float
    avg_price: float
    last_price: Optional[float] = None
    market_value: float
    weight_pct: float
    unrealized_pnl: Optional[float] = None
    sector: Optional[str] = None
    opened_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        from bist_signal_bot.data.symbol_utils import normalize_symbol
        return normalize_symbol(v)

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v

    @field_validator("avg_price")
    @classmethod
    def validate_avg_price(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Average price must be greater than zero")
        return v

    @field_validator("market_value")
    @classmethod
    def validate_market_value(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Market value cannot be negative")
        return v

    @field_validator("weight_pct")
    @classmethod
    def validate_weight_pct(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Weight percentage cannot be negative")
        return v

class PortfolioState(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    equity: float
    cash: float
    holdings: list[PortfolioHolding] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    daily_signal_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("equity")
    @classmethod
    def validate_equity(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Equity must be positive")
        return v

    @field_validator("cash")
    @classmethod
    def validate_cash(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Cash cannot be negative")
        return v

    @field_validator("daily_signal_count")
    @classmethod
    def validate_daily_signal_count(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Daily signal count cannot be negative")
        return v

    def holding_symbols(self) -> list[str]:
        return [h.symbol for h in self.holdings]

    def gross_exposure_pct(self) -> float:
        if self.equity <= 0:
            return 0.0
        total_market_value = sum(h.market_value for h in self.holdings)
        return total_market_value / self.equity

    def net_exposure_pct(self) -> float:
        if self.equity <= 0:
            return 0.0
        net_market_value = 0.0
        for h in self.holdings:
            if h.side == PortfolioPositionSide.LONG:
                net_market_value += h.market_value
            elif h.side == PortfolioPositionSide.SHORT:
                net_market_value -= h.market_value
        return net_market_value / self.equity

    def open_position_count(self) -> int:
        return len(self.holdings)

    def sector_weights(self) -> dict[str, float]:
        if self.equity <= 0:
            return {}
        weights: dict[str, float] = {}
        for h in self.holdings:
            sector = h.sector or "UNKNOWN"
            weights[sector] = weights.get(sector, 0.0) + (h.market_value / self.equity)
        return weights

    def symbol_weight(self, symbol: str) -> float:
        from bist_signal_bot.data.symbol_utils import normalize_symbol
        norm_sym = normalize_symbol(symbol)
        for h in self.holdings:
            if h.symbol == norm_sym:
                return h.market_value / self.equity
        return 0.0

@dataclass
class CorrelationMatrixResult:
    symbols: list[str]
    matrix: "pd.DataFrame"
    lookback_rows: int
    method: str
    generated_at: datetime
    issues: list[str]
    metadata: dict[str, Any]

    def summary(self) -> dict[str, Any]:
        return {
            "symbol_count": len(self.symbols),
            "lookback_rows": self.lookback_rows,
            "method": self.method,
            "issues_count": len(self.issues)
        }

@dataclass
class ExposureReport:
    gross_exposure_pct: float
    net_exposure_pct: float
    long_exposure_pct: float
    short_exposure_pct: float
    max_symbol_weight_pct: float
    sector_weights: dict[str, float]
    open_position_count: int
    cash_pct: float
    issues: list[str]
    metadata: dict[str, Any]

    def summary(self) -> dict[str, Any]:
        return {
            "gross_exposure_pct": self.gross_exposure_pct,
            "net_exposure_pct": self.net_exposure_pct,
            "max_symbol_weight_pct": self.max_symbol_weight_pct,
            "open_position_count": self.open_position_count,
            "cash_pct": self.cash_pct,
            "issues_count": len(self.issues)
        }

class AllocationRequest(BaseModel):
    signals: list[SignalCandidate]
    risk_decisions: list[RiskDecision]
    portfolio_state: PortfolioState
    method: AllocationMethod
    total_allocation_pct: float
    max_symbol_weight_pct: float
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("total_allocation_pct")
    @classmethod
    def validate_total_allocation_pct(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Total allocation percentage must be between 0.0 and 1.0")
        return v

    @field_validator("max_symbol_weight_pct")
    @classmethod
    def validate_max_symbol_weight_pct(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Max symbol weight percentage must be between 0.0 and 1.0")
        return v

    @model_validator(mode="after")
    def validate_signals_and_risks(self) -> "AllocationRequest":
        return self

@dataclass
class AllocationResultItem:
    symbol: str
    approved: bool
    original_notional: Optional[float]
    allocated_notional: float
    allocated_weight_pct: float
    quantity: float
    reduction_pct: float
    reasons: list[str]
    metadata: dict[str, Any]

@dataclass
class AllocationResult:
    method: AllocationMethod
    items: list[AllocationResultItem]
    total_allocated_notional: float
    total_allocated_pct: float
    rejected_symbols: list[str]
    reduced_symbols: list[str]
    issues: list[str]
    generated_at: datetime

    def summary(self) -> dict[str, Any]:
        return {
            "method": self.method.value,
            "total_allocated_pct": self.total_allocated_pct,
            "items_count": len(self.items),
            "approved_count": len([i for i in self.items if i.approved]),
            "rejected_count": len(self.rejected_symbols),
            "reduced_count": len(self.reduced_symbols)
        }

@dataclass
class PortfolioRiskDecision:
    portfolio_state: PortfolioState
    input_signals: list[SignalCandidate]
    trade_risk_decisions: list[RiskDecision]
    allocation_result: AllocationResult
    exposure_report_before: ExposureReport
    exposure_report_after: Optional[ExposureReport]
    correlation_result: Optional[CorrelationMatrixResult]
    status: PortfolioDecisionStatus
    approved_count: int
    rejected_count: int
    reduced_count: int
    reject_reasons: list[PortfolioRejectReason]
    warnings: list[str]
    generated_at: datetime
    disclaimer: str = "Portfolio risk research output only. Not investment advice. No order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "approved_count": self.approved_count,
            "rejected_count": self.rejected_count,
            "reduced_count": self.reduced_count,
            "disclaimer": self.disclaimer
        }

    def safe_public_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "approved_count": self.approved_count,
            "rejected_count": self.rejected_count,
            "reduced_count": self.reduced_count,
            "allocation_method": self.allocation_result.method.value,
            "total_allocated_pct": self.allocation_result.total_allocated_pct,
            "gross_exposure_before_pct": self.exposure_report_before.gross_exposure_pct,
            "gross_exposure_after_pct": self.exposure_report_after.gross_exposure_pct if self.exposure_report_after else None,
            "disclaimer": self.disclaimer
        }
