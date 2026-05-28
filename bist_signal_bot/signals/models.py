from datetime import datetime
from enum import Enum
from typing import Any, List, Dict, Optional
from pydantic import BaseModel, Field, field_validator


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
    model_config = {"arbitrary_types_allowed": True}
    category: str
    message: str
    score_impact: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)

class RiskNote(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    category: str
    message: str
    severity: str = "info"
    metadata: dict[str, Any] = Field(default_factory=dict)

class SignalCandidate(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
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
    breadth_context_id: str | None = None
    breadth_regime_label: str | None = None
    participation_score: float | None = None
    sector_breadth_status: str | None = None
    divergence_warning: str | None = None
    disclaimer: str = "Research signal candidate only. Not investment advice. No order was sent."

    @field_validator("symbol", mode='before')
    def normalize_symbol(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.upper().strip()
            if v.endswith(".IS"):
                v = v[:-3]
        return v

    @field_validator("strategy_name")
    def validate_strategy_name(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("strategy_name cannot be empty")
        return str(v).lower().replace(" ", "_")

    @field_validator("risk_reward")
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
    model_config = {"arbitrary_types_allowed": True}
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

class SignalLifecycleState(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    WATCHING = "WATCHING"
    MUTED = "MUTED"
    COOLDOWN = "COOLDOWN"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
    ERROR = "ERROR"

class SignalLifecycleEventType(str, Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    ALERT_SENT = "ALERT_SENT"
    ALERT_MUTED = "ALERT_MUTED"
    COOLDOWN_STARTED = "COOLDOWN_STARTED"
    COOLDOWN_ENDED = "COOLDOWN_ENDED"
    WATCHLIST_ADDED = "WATCHLIST_ADDED"
    WATCHLIST_REMOVED = "WATCHLIST_REMOVED"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"
    OUTCOME_UPDATED = "OUTCOME_UPDATED"
    EXIT_SIMULATED = "EXIT_SIMULATED"
    ARCHIVED = "ARCHIVED"
    MANUAL_NOTE = "MANUAL_NOTE"
    ERROR = "ERROR"

class SignalAlertDecision(str, Enum):
    SEND = "SEND"
    MUTE_DUPLICATE = "MUTE_DUPLICATE"
    MUTE_COOLDOWN = "MUTE_COOLDOWN"
    MUTE_LOW_PRIORITY = "MUTE_LOW_PRIORITY"
    MUTE_UNCHANGED = "MUTE_UNCHANGED"
    SEND_DIGEST_ONLY = "SEND_DIGEST_ONLY"
    BLOCK_SECURITY = "BLOCK_SECURITY"
    SKIP = "SKIP"

class SignalPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class SignalOutcomeState(str, Enum):
    NOT_TRACKED = "NOT_TRACKED"
    PENDING = "PENDING"
    HIT_RESEARCH_TARGET = "HIT_RESEARCH_TARGET"
    HIT_RESEARCH_STOP = "HIT_RESEARCH_STOP"
    TIME_EXPIRED = "TIME_EXPIRED"
    INVALIDATED_BY_RISK = "INVALIDATED_BY_RISK"
    INVALIDATED_BY_REGIME = "INVALIDATED_BY_REGIME"
    INVALIDATED_BY_BREADTH = "INVALIDATED_BY_BREADTH"
    INVALIDATED_BY_DATA = "INVALIDATED_BY_DATA"
    MANUAL_CLOSED = "MANUAL_CLOSED"
    UNKNOWN = "UNKNOWN"

class ResearchExitRuleType(str, Enum):
    FIXED_PERCENT_TARGET = "FIXED_PERCENT_TARGET"
    FIXED_PERCENT_STOP = "FIXED_PERCENT_STOP"
    ATR_MULTIPLE_TARGET = "ATR_MULTIPLE_TARGET"
    ATR_MULTIPLE_STOP = "ATR_MULTIPLE_STOP"
    TRAILING_PERCENT = "TRAILING_PERCENT"
    TIME_STOP = "TIME_STOP"
    SIGNAL_REVERSAL = "SIGNAL_REVERSAL"
    REGIME_INVALIDATION = "REGIME_INVALIDATION"
    RISK_INVALIDATION = "RISK_INVALIDATION"
    NONE = "NONE"

class SignalFingerprint(BaseModel):
    fingerprint_id: str
    symbol: str
    strategy_name: Optional[str] = None
    signal_direction: Optional[str] = None
    source_type: Optional[str] = None
    timeframe: Optional[str] = None
    normalized_payload_hash: str
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TrackedSignal(BaseModel):
    valuation_context_id: Optional[str] = None
    valuation_score: Optional[float] = None
    valuation_risk_level: Optional[str] = None
    expensive_metric_count: Optional[int] = None
    cheap_metric_count: Optional[int] = None
    signal_id: str
    fingerprint_id: str
    symbol: str
    strategy_name: Optional[str] = None
    source_type: str
    timeframe: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    valid_until: Optional[datetime] = None
    state: SignalLifecycleState = SignalLifecycleState.NEW
    priority: SignalPriority = SignalPriority.NORMAL
    direction: Optional[str] = None
    initial_score: Optional[float] = None
    current_score: Optional[float] = None
    confidence: Optional[float] = None
    consensus_score: Optional[float] = None
    risk_decision: Optional[str] = None
    regime: Optional[str] = None
    breadth_status: Optional[str] = None
    fundamental_score: Optional[float] = None
    ml_score: Optional[float] = None
    watchlist: bool = False
    alert_count: int = 0
    last_alert_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    outcome_state: SignalOutcomeState = SignalOutcomeState.NOT_TRACKED
    outcome_return_pct: Optional[float] = None
    reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = "Tracked signal is research-only. Not investment advice. No real order was sent."

    def summary(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "strategy": self.strategy_name,
            "state": self.state,
            "priority": self.priority,
            "direction": self.direction,
            "current_score": self.current_score,
            "outcome": self.outcome_state,
        }

    def safe_public_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        # Omit potentially sensitive fields for public output
        data.pop("metadata", None)
        return data

class SignalLifecycleEvent(BaseModel):
    event_id: str
    signal_id: str
    event_type: SignalLifecycleEventType
    previous_state: Optional[SignalLifecycleState] = None
    new_state: Optional[SignalLifecycleState] = None
    timestamp: datetime
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SignalAlertPolicy(BaseModel):
    dedupe_enabled: bool = True
    cooldown_minutes: int = 240
    validity_minutes: int = 1440
    min_score_change_for_repeat_alert: float = 7.5
    min_confidence_for_alert: float = 45.0
    max_alerts_per_signal: int = 3
    digest_only_below_priority: SignalPriority = SignalPriority.NORMAL
    mute_low_agreement: bool = True
    mute_high_conflict: bool = True
    allow_critical_repeat: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AlertEvaluationResult(BaseModel):
    signal_id: Optional[str] = None
    fingerprint_id: str
    decision: SignalAlertDecision
    should_send: bool
    should_add_to_digest: bool
    reason: str
    cooldown_remaining_minutes: Optional[float] = None
    previous_signal_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WatchlistEntry(BaseModel):
    watchlist_id: str
    signal_id: str
    symbol: str
    strategy_name: Optional[str] = None
    added_at: datetime
    expires_at: Optional[datetime] = None
    priority: SignalPriority = SignalPriority.NORMAL
    notes: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ResearchExitRule(BaseModel):
    rule_id: str
    rule_type: ResearchExitRuleType
    value: Optional[float] = None
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ResearchExitSimulation(BaseModel):
    simulation_id: str
    signal_id: str
    symbol: str
    started_at: datetime
    evaluated_at: datetime
    entry_reference_price: Optional[float] = None
    current_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_price: Optional[float] = None
    trailing_level: Optional[float] = None
    triggered_rule: ResearchExitRuleType
    outcome_state: SignalOutcomeState
    simulated_return_pct: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Exit simulation is research-only. It is not a real order. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SignalLifecycleSummary(BaseModel):
    total_signals: int = 0
    active_count: int = 0
    watching_count: int = 0
    muted_count: int = 0
    expired_count: int = 0
    invalidated_count: int = 0
    completed_count: int = 0
    alerts_sent: int = 0
    alerts_muted: int = 0
    watchlist_count: int = 0
    generated_at: datetime
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
