from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Dict, Optional
from pydantic import BaseModel, Field, field_validator
from bist_signal_bot.signals.models import SignalCandidate

class RiskDecisionStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REDUCED = "REDUCED"
    WATCH_ONLY = "WATCH_ONLY"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class RiskRejectReason(str, Enum):
    SCORE_TOO_LOW = "SCORE_TOO_LOW"
    CONFIDENCE_TOO_LOW = "CONFIDENCE_TOO_LOW"
    RISK_REWARD_TOO_LOW = "RISK_REWARD_TOO_LOW"
    POSITION_TOO_SMALL = "POSITION_TOO_SMALL"
    POSITION_TOO_LARGE = "POSITION_TOO_LARGE"
    INSUFFICIENT_CAPITAL = "INSUFFICIENT_CAPITAL"
    MAX_POSITION_LIMIT_EXCEEDED = "MAX_POSITION_LIMIT_EXCEEDED"
    PORTFOLIO_RISK_LIMIT_EXCEEDED = "PORTFOLIO_RISK_LIMIT_EXCEEDED"
    SYMBOL_ALREADY_HELD = "SYMBOL_ALREADY_HELD"
    DAILY_SIGNAL_LIMIT_EXCEEDED = "DAILY_SIGNAL_LIMIT_EXCEEDED"
    LIQUIDITY_TOO_LOW = "LIQUIDITY_TOO_LOW"
    VOLATILITY_TOO_HIGH = "VOLATILITY_TOO_HIGH"
    STOP_INVALID = "STOP_INVALID"
    TARGET_INVALID = "TARGET_INVALID"
    COST_TOO_HIGH = "COST_TOO_HIGH"
    UNKNOWN = "UNKNOWN"

class PositionSizingMethod(str, Enum):
    FIXED_NOTIONAL = "FIXED_NOTIONAL"
    EQUITY_PERCENT = "EQUITY_PERCENT"
    RISK_PERCENT = "RISK_PERCENT"
    ATR_RISK = "ATR_RISK"
    VOLATILITY_TARGET = "VOLATILITY_TARGET"
    KELLY_FRACTIONAL = "KELLY_FRACTIONAL"
    SCORE_WEIGHTED = "SCORE_WEIGHTED"

class StopMethod(str, Enum):
    NONE = "NONE"
    FIXED_PERCENT = "FIXED_PERCENT"
    ATR_MULTIPLE = "ATR_MULTIPLE"
    RECENT_SWING = "RECENT_SWING"
    VOLATILITY_BASED = "VOLATILITY_BASED"

class TargetMethod(str, Enum):
    NONE = "NONE"
    FIXED_PERCENT = "FIXED_PERCENT"
    RISK_REWARD_MULTIPLE = "RISK_REWARD_MULTIPLE"
    ATR_MULTIPLE = "ATR_MULTIPLE"
    RECENT_RESISTANCE_SUPPORT = "RECENT_RESISTANCE_SUPPORT"

class RiskSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"

class RiskContext(BaseModel):
    equity: float
    available_cash: float
    current_positions: dict[str, Any] = Field(default_factory=dict)
    open_position_count: int = 0
    daily_signal_count: int = 0
    portfolio_risk_pct: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("equity")
    @classmethod
    def validate_equity(cls, v):
        if v <= 0:
            raise ValueError("equity must be > 0")
        return v

    @field_validator("available_cash")
    @classmethod
    def validate_available_cash(cls, v):
        if v < 0:
            raise ValueError("available_cash must be >= 0")
        return v

    @field_validator("open_position_count")
    @classmethod
    def validate_open_position_count(cls, v):
        if v < 0:
            raise ValueError("open_position_count must be >= 0")
        return v

    @field_validator("daily_signal_count")
    @classmethod
    def validate_daily_signal_count(cls, v):
        if v < 0:
            raise ValueError("daily_signal_count must be >= 0")
        return v

    @field_validator("portfolio_risk_pct")
    @classmethod
    def validate_portfolio_risk_pct(cls, v):
        if v < 0:
            raise ValueError("portfolio_risk_pct must be >= 0")
        return v

class StopTargetReference(BaseModel):
    entry_price: float
    stop_price: float | None = None
    target_price: float | None = None
    risk_per_share: float | None = None
    reward_per_share: float | None = None
    risk_reward: float | None = None
    stop_method: StopMethod = StopMethod.NONE
    target_method: TargetMethod = TargetMethod.NONE
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("entry_price")
    @classmethod
    def validate_entry_price(cls, v):
        if v <= 0:
            raise ValueError("entry_price must be > 0")
        return v

    @field_validator("stop_price", "target_price")
    @classmethod
    def validate_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("stop and target prices must be > 0")
        return v

    @field_validator("risk_per_share", "reward_per_share", "risk_reward")
    @classmethod
    def validate_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("risk/reward values cannot be negative")
        return v

class PositionSizeResult(BaseModel):
    method: PositionSizingMethod
    symbol: str
    side: RiskSide
    equity: float
    entry_price: float
    stop_price: float | None = None
    target_risk_pct: float = 0.0
    max_position_pct: float = 0.0
    raw_notional: float = 0.0
    capped_notional: float = 0.0
    quantity: float = 0.0
    estimated_cost: float = 0.0
    final_notional: float = 0.0
    final_position_pct: float = 0.0
    risk_amount: float | None = None
    risk_pct: float | None = None
    reduced: bool = False
    issues: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("entry_price", "equity")
    @classmethod
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError("Value must be > 0")
        return v

    @field_validator("quantity", "final_notional", "final_position_pct")
    @classmethod
    def validate_non_negative(cls, v):
        if v < 0:
            raise ValueError("Value must be >= 0")
        return v

class RiskFilterResult(BaseModel):
    passed: bool
    status: RiskDecisionStatus
    reject_reasons: list[RiskRejectReason] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    score_adjustment: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)

class RiskDecision(BaseModel):
    signal: SignalCandidate
    status: RiskDecisionStatus
    side: RiskSide
    approved: bool
    position_size: PositionSizeResult | None = None
    stop_target: StopTargetReference | None = None
    filter_result: RiskFilterResult
    final_score: float = 0.0
    final_confidence: float = 0.0
    max_loss_amount: float | None = None
    max_loss_pct: float | None = None
    estimated_total_cost: float | None = None
    estimated_cost_bps: float | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    disclaimer: str = "Risk decision research output only. Not investment advice. No order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "symbol": self.signal.symbol,
            "strategy": self.signal.strategy_name,
            "side": self.side.value,
            "status": self.status.value,
            "approved": self.approved,
            "final_score": round(self.final_score, 2),
            "final_confidence": round(self.final_confidence, 2),
            "position_notional": round(self.position_size.final_notional, 2) if self.position_size else None,
            "quantity": self.position_size.quantity if self.position_size else None,
            "entry_price": self.stop_target.entry_price if self.stop_target else None,
            "stop_price": self.stop_target.stop_price if self.stop_target else None,
            "target_price": self.stop_target.target_price if self.stop_target else None,
            "risk_reward": round(self.stop_target.risk_reward, 2) if self.stop_target and self.stop_target.risk_reward else None,
            "max_loss_amount": round(self.max_loss_amount, 2) if self.max_loss_amount else None,
            "estimated_cost": round(self.estimated_total_cost, 2) if self.estimated_total_cost else None,
            "reject_reasons": [r.value for r in self.filter_result.reject_reasons],
            "warnings": self.filter_result.warnings,
            "generated_at": self.generated_at.isoformat(),
            "disclaimer": self.disclaimer
        }

    def safe_public_dict(self) -> dict[str, Any]:
        d = self.summary()
        return d

class RiskBatchResult(BaseModel):
    decisions: list[RiskDecision] = Field(default_factory=list)
    requested_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    reduced_count: int = 0
    watch_only_count: int = 0
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    elapsed_seconds: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "requested_count": self.requested_count,
            "approved_count": self.approved_count,
            "rejected_count": self.rejected_count,
            "reduced_count": self.reduced_count,
            "watch_only_count": self.watch_only_count,
            "generated_at": self.generated_at.isoformat(),
            "elapsed_seconds": round(self.elapsed_seconds, 2)
        }
