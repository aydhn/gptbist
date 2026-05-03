from datetime import datetime
from enum import Enum
from typing import Any, List, Dict, Optional
from pydantic import BaseModel, Field, validator


class SignalDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"
    WATCH = "WATCH"
    AVOID = "AVOID"
    UNKNOWN = "UNKNOWN"

class SignalStrength(str, Enum):
    VERY_WEAK = "VERY_WEAK"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"
    UNKNOWN = "UNKNOWN"

class SignalStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    FILTERED = "FILTERED"
    REJECTED = "REJECTED"
    CONFIRMED = "CONFIRMED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"

class SignalTimeframe(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    INTRADAY = "INTRADAY"
    MULTI = "MULTI"

class SignalReason(BaseModel):
    category: str
    message: str
    score_impact: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)

class RiskNote(BaseModel):
    category: str
    message: str
    severity: str = "info"
    metadata: dict[str, Any] = Field(default_factory=dict)

class SignalCandidate(BaseModel):
    symbol: str
    strategy_name: str
    direction: SignalDirection
    status: SignalStatus = SignalStatus.CANDIDATE
    strength: SignalStrength = SignalStrength.UNKNOWN
    score: float = Field(ge=0.0, le=100.0, default=0.0)
    confidence: float = Field(ge=0.0, le=100.0, default=0.0)
    timeframe: str = "1d"
    generated_at: datetime = Field(default_factory=datetime.now)
    signal_bar_timestamp: datetime | None = None
    entry_reference_price: float | None = None
    stop_reference_price: float | None = None
    target_reference_price: float | None = None
    risk_reward: float | None = None
    reasons: list[SignalReason] = Field(default_factory=list)
    risk_notes: list[RiskNote] = Field(default_factory=list)
    feature_snapshot: dict[str, Any] = Field(default_factory=dict)
    params: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = "Research signal candidate only. Not investment advice. No order was sent."

    @validator("symbol", pre=True)
    def normalize_symbol(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.upper().strip()
            if v.endswith(".IS"):
                v = v[:-3]
        return v

    @validator("strategy_name")
    def validate_strategy_name(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("strategy_name cannot be empty")
        return str(v).lower().replace(" ", "_")

    @validator("risk_reward")
    def validate_risk_reward(cls, v: float | None) -> float | None:
        if v is not None and v < 0:
            raise ValueError("risk_reward cannot be negative")
        return v

    def is_actionable_candidate(self) -> bool:
        return (
            self.direction in (SignalDirection.LONG, SignalDirection.SHORT) and
            self.status in (SignalStatus.CANDIDATE, SignalStatus.CONFIRMED)
        )

    def summary(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "strategy": self.strategy_name,
            "direction": self.direction.value,
            "status": self.status.value,
            "strength": self.strength.value,
            "score": round(self.score, 2),
            "confidence": round(self.confidence, 2),
            "timeframe": self.timeframe,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "signal_bar_timestamp": self.signal_bar_timestamp.isoformat() if self.signal_bar_timestamp else None,
            "entry_reference_price": self.entry_reference_price,
            "risk_reward": round(self.risk_reward, 2) if self.risk_reward else None,
            "reasons_count": len(self.reasons),
            "risk_notes_count": len(self.risk_notes),
            "actionable": self.is_actionable_candidate()
        }

    def safe_public_dict(self) -> dict[str, Any]:
        d = self.model_dump(exclude={"feature_snapshot", "params", "metadata"})
        return d

class StrategySignalBatch(BaseModel):
    strategy_name: str
    symbol_count: int = 0
    candidates: list[SignalCandidate] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)
    elapsed_seconds: float = 0.0
    success_count: int = 0
    failed_count: int = 0
    issues: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def long_count(self) -> int:
        return sum(1 for c in self.candidates if c.direction == SignalDirection.LONG)

    def short_count(self) -> int:
        return sum(1 for c in self.candidates if c.direction == SignalDirection.SHORT)

    def watch_count(self) -> int:
        return sum(1 for c in self.candidates if c.direction == SignalDirection.WATCH)

    def summary(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy_name,
            "symbol_count": self.symbol_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "candidates_count": len(self.candidates),
            "long_count": self.long_count(),
            "short_count": self.short_count(),
            "watch_count": self.watch_count(),
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "generated_at": self.generated_at.isoformat()
        }
