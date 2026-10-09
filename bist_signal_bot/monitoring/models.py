from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional, List, Dict

class MonitoringStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    DEGRADED = "DEGRADED"
    FAIL = "FAIL"
    BLOCKED_RESEARCH = "BLOCKED_RESEARCH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"

class MonitoringObjectType(str, Enum):
    STRATEGY = "STRATEGY"
    MODEL = "MODEL"
    FEATURE_SET = "FEATURE_SET"
    SIGNAL_FAMILY = "SIGNAL_FAMILY"
    PORTFOLIO_RESEARCH = "PORTFOLIO_RESEARCH"
    CALIBRATION_POLICY = "CALIBRATION_POLICY"
    CONTEXT_LAYER = "CONTEXT_LAYER"
    CUSTOM = "CUSTOM"

class MonitoringWindow(str, Enum):
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"
    CUSTOM = "CUSTOM"

class DecayType(str, Enum):
    PERFORMANCE_DECAY = "PERFORMANCE_DECAY"
    CALIBRATION_DECAY = "CALIBRATION_DECAY"
    WIN_RATE_DECAY = "WIN_RATE_DECAY"
    EXPECTANCY_DECAY = "EXPECTANCY_DECAY"
    RISK_ADJUSTED_DECAY = "RISK_ADJUSTED_DECAY"
    HIT_RATE_DECAY = "HIT_RATE_DECAY"
    FEATURE_DRIFT_LINKED_DECAY = "FEATURE_DRIFT_LINKED_DECAY"
    MODEL_DRIFT_LINKED_DECAY = "MODEL_DRIFT_LINKED_DECAY"
    SAMPLE_QUALITY_DECAY = "SAMPLE_QUALITY_DECAY"
    UNKNOWN = "UNKNOWN"

class ChampionChallengerDecision(str, Enum):
    KEEP_CHAMPION = "KEEP_CHAMPION"
    WATCH_CHAMPION = "WATCH_CHAMPION"
    PROMOTE_CHALLENGER_RESEARCH = "PROMOTE_CHALLENGER_RESEARCH"
    REJECT_CHALLENGER = "REJECT_CHALLENGER"
    NEEDS_MORE_DATA = "NEEDS_MORE_DATA"
    ESCALATE_REVIEW = "ESCALATE_REVIEW"
    UNKNOWN = "UNKNOWN"

class MonitoringAlertType(str, Enum):
    STRATEGY_DEGRADED = "STRATEGY_DEGRADED"
    MODEL_DEGRADED = "MODEL_DEGRADED"
    CALIBRATION_DECAY = "CALIBRATION_DECAY"
    FEATURE_DRIFT = "FEATURE_DRIFT"
    MODEL_DRIFT = "MODEL_DRIFT"
    LOW_SAMPLE = "LOW_SAMPLE"
    STALE_OUTCOMES = "STALE_OUTCOMES"
    QUALITY_GATE_FAIL = "QUALITY_GATE_FAIL"
    CHAMPION_CHALLENGER_CHANGE = "CHAMPION_CHALLENGER_CHANGE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    CUSTOM = "CUSTOM"

class MonitoringMetric(BaseModel):
    metric_id: str
    object_type: MonitoringObjectType
    object_id: str
    metric_name: str
    window: MonitoringWindow
    value: Optional[float] = None
    baseline_value: Optional[float] = None
    delta: Optional[float] = None
    sample_count: Optional[int] = None
    as_of: datetime
    status: MonitoringStatus
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MonitoringSnapshot(BaseModel):
    snapshot_id: str
    object_type: MonitoringObjectType
    object_id: str
    as_of: datetime
    metrics: List[MonitoringMetric] = Field(default_factory=list)
    status: MonitoringStatus
    health_score: Optional[float] = None
    sample_count: Optional[int] = None
    key_findings: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Monitoring snapshot is local research performance metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PerformanceDecayFinding(BaseModel):
    decay_id: str
    object_type: MonitoringObjectType
    object_id: str
    decay_type: DecayType
    metric_name: str
    baseline_value: Optional[float] = None
    current_value: Optional[float] = None
    decay_score: Optional[float] = None
    status: MonitoringStatus
    message: str
    evidence_refs: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Performance decay finding is research-only metadata. It does not predict future returns or authorize trading. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChampionChallengerComparison(BaseModel):
    comparison_id: str
    object_type: MonitoringObjectType
    champion_id: str
    challenger_id: str
    as_of: datetime
    champion_metrics: List[MonitoringMetric] = Field(default_factory=list)
    challenger_metrics: List[MonitoringMetric] = Field(default_factory=list)
    decision: ChampionChallengerDecision
    decision_score: Optional[float] = None
    reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Champion/challenger comparison is local research governance metadata only. It is not investment advice or live deployment approval. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MonitoringAlert(BaseModel):
    alert_id: str
    alert_type: MonitoringAlertType
    object_type: MonitoringObjectType
    object_id: str
    severity: str
    status: MonitoringStatus
    created_at: datetime
    title: str
    message: str
    evidence_refs: List[str] = Field(default_factory=list)
    routed_to: List[str] = Field(default_factory=list)
    review_case_id: Optional[str] = None
    acknowledged: bool = False
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Monitoring alert is local research review metadata only. It is not a trading alert or order instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MonitoringWatchlistItem(BaseModel):
    watch_id: str
    object_type: MonitoringObjectType
    object_id: str
    added_at: datetime
    reason: str
    status: MonitoringStatus
    latest_snapshot_id: Optional[str] = None
    latest_alert_id: Optional[str] = None
    review_case_id: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MonitoringReport(BaseModel):
    report_id: str
    generated_at: datetime
    snapshots: List[MonitoringSnapshot] = Field(default_factory=list)
    decay_findings: List[PerformanceDecayFinding] = Field(default_factory=list)
    champion_challenger: List[ChampionChallengerComparison] = Field(default_factory=list)
    alerts: List[MonitoringAlert] = Field(default_factory=list)
    watchlist: List[MonitoringWatchlistItem] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Monitoring report is local research monitoring output only. It is not investment advice, portfolio advice, or a trading instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)


# --- Operational heartbeat models (used by monitoring/heartbeat.py) ---
from pydantic import model_validator

class HealthLevel(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class MonitoringComponent(Enum):
    RUNTIME = "RUNTIME"
    SCHEDULER = "SCHEDULER"
    DATA = "DATA"
    SCANNER = "SCANNER"
    STRATEGY = "STRATEGY"
    RISK = "RISK"
    PORTFOLIO_RISK = "PORTFOLIO_RISK"
    REGIME = "REGIME"
    ML = "ML"
    PAPER = "PAPER"
    TELEGRAM = "TELEGRAM"
    STORAGE = "STORAGE"
    LOCK = "LOCK"
    CONFIG = "CONFIG"
    HEALTHCHECK = "HEALTHCHECK"
    UNKNOWN = "UNKNOWN"

class HeartbeatRecord(BaseModel):
    heartbeat_id: str = Field(...)
    timestamp: datetime = Field(...)
    component: MonitoringComponent = Field(...)
    status: HealthLevel = Field(...)
    message: str = Field(...)
    runtime_run_id: str | None = Field(default=None)
    scheduler_active: bool = Field(default=False)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_heartbeat(self):
        if not self.heartbeat_id:
            raise ValueError("heartbeat_id cannot be empty")
        if self.message is None:
            raise ValueError("message cannot be None")
        return self
