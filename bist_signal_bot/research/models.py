import re
from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator

class ResearchRunType(str, Enum):
    BACKTEST = "BACKTEST"
    OPTIMIZATION = "OPTIMIZATION"
    WALK_FORWARD = "WALK_FORWARD"
    SIGNAL_SCAN = "SIGNAL_SCAN"
    PAPER_TRADING = "PAPER_TRADING"
    ML_DATASET = "ML_DATASET"
    ML_TRAINING = "ML_TRAINING"
    ML_INFERENCE = "ML_INFERENCE"
    REGIME_ANALYSIS = "REGIME_ANALYSIS"
    RUNTIME_PIPELINE = "RUNTIME_PIPELINE"
    ADAPTIVE_RECOMMENDATION = "ADAPTIVE_RECOMMENDATION"
    MONITORING_DIAGNOSTIC = "MONITORING_DIAGNOSTIC"
    QUALITY_GATE = "QUALITY_GATE"
    SECURITY_AUDIT = "SECURITY_AUDIT"
    PERFORMANCE_BENCHMARK = "PERFORMANCE_BENCHMARK"
    MANUAL_NOTE = "MANUAL_NOTE"
    UNKNOWN = "UNKNOWN"

class ResearchRunStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    WATCH_ONLY = "WATCH_ONLY"
    UNKNOWN = "UNKNOWN"

class ResearchArtifactType(str, Enum):
    JSON = "JSON"
    CSV = "CSV"
    MARKDOWN = "MARKDOWN"
    MODEL = "MODEL"
    LEDGER = "LEDGER"
    REPORT = "REPORT"
    CONFIG = "CONFIG"
    DATASET = "DATASET"
    OTHER = "OTHER"

class ResearchSignalOutcome(str, Enum):
    NOT_TRACKED = "NOT_TRACKED"
    PENDING = "PENDING"
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"

class AttributionGroupBy(str, Enum):
    SYMBOL = "SYMBOL"
    STRATEGY = "STRATEGY"
    PARAMETER_SET = "PARAMETER_SET"
    REGIME = "REGIME"
    ML_SCORE_BUCKET = "ML_SCORE_BUCKET"
    RISK_DECISION = "RISK_DECISION"
    PORTFOLIO_DECISION = "PORTFOLIO_DECISION"
    TIMEFRAME = "TIMEFRAME"
    RUN_TYPE = "RUN_TYPE"

class ResearchTag(BaseModel):
    tag: str
    category: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("tag")
    @classmethod
    def validate_tag(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Tag cannot be empty")
        v = v.strip().lower()
        if re.search(r'(token|secret|key|password|bearer|auth|apikey)', v):
            raise ValueError("Tag looks like a secret or forbidden keyword")
        return v

class ResearchArtifactRef(BaseModel):
    artifact_id: str
    artifact_type: ResearchArtifactType
    path: str
    description: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Path cannot be empty")
        if ".." in v or v.startswith("/etc") or v.startswith("/root") or v.startswith("/var"):
             raise ValueError("Unsafe path detected")
        return v

    @field_validator("artifact_id")
    @classmethod
    def validate_artifact_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Artifact ID cannot be empty")
        return v

class ResearchLineageRef(BaseModel):
    parent_run_id: str | None = None
    source_run_ids: list[str] = Field(default_factory=list)
    source_artifact_ids: list[str] = Field(default_factory=list)
    related_signal_ids: list[str] = Field(default_factory=list)
    related_order_ids: list[str] = Field(default_factory=list)
    related_fill_ids: list[str] = Field(default_factory=list)
    related_model_ids: list[str] = Field(default_factory=list)
    related_recommendation_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ResearchRun(BaseModel):
    run_id: str
    run_type: ResearchRunType
    status: ResearchRunStatus
    title: str
    strategy_name: str | None = None
    symbols: list[str] = Field(default_factory=list)
    timeframe: str | None = None
    source: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    tags: list[ResearchTag] = Field(default_factory=list)
    artifacts: list[ResearchArtifactRef] = Field(default_factory=list)
    lineage: ResearchLineageRef = Field(default_factory=ResearchLineageRef)
    started_at: datetime
    finished_at: datetime | None = None
    elapsed_seconds: float | None = None
    warnings: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    disclaimer: str = "Research run output only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_type": self.run_type.value,
            "status": self.status.value,
            "title": self.title,
            "strategy": self.strategy_name,
            "symbols": len(self.symbols),
            "metrics": self.metrics,
            "elapsed_seconds": self.elapsed_seconds,
            "started_at": self.started_at.isoformat() if self.started_at else None
        }

    def safe_public_dict(self) -> dict[str, Any]:
        data = self.model_dump()
        # Ensure no secrets in output
        data.pop("params", None)
        return data

class ResearchLedgerEntry(BaseModel):
    entry_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    run: ResearchRun
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class SignalJournalEntry(BaseModel):
    journal_id: str
    signal_id: str | None = None
    run_id: str | None = None
    symbol: str
    strategy_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    direction: str | None = None
    signal_score: float | None = None
    confidence: float | None = None
    final_score: float | None = None
    ml_score: float | None = None
    regime: str | None = None
    risk_decision: str | None = None
    portfolio_decision: str | None = None
    paper_order_id: str | None = None
    paper_fill_id: str | None = None
    outcome: ResearchSignalOutcome = ResearchSignalOutcome.NOT_TRACKED
    outcome_horizon_bars: int | None = None
    outcome_return_pct: float | None = None
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    tags: list[ResearchTag] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "journal_id": self.journal_id,
            "symbol": self.symbol,
            "strategy": self.strategy_name,
            "direction": self.direction,
            "outcome": self.outcome.value,
            "timestamp": self.timestamp.isoformat()
        }

class ResearchComparisonItem(BaseModel):
    run_id: str
    run_type: ResearchRunType
    label: str
    metrics: dict[str, Any]
    rank: int | None = None
    score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class ResearchComparisonReport(BaseModel):
    comparison_id: str
    title: str
    items: list[ResearchComparisonItem]
    sort_metric: str | None = None
    best_run_id: str | None = None
    worst_run_id: str | None = None
    findings: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    disclaimer: str = "Research comparison output only. Past results do not guarantee future performance. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "items_count": len(self.items),
            "best_run_id": self.best_run_id,
            "worst_run_id": self.worst_run_id
        }

class AttributionBucket(BaseModel):
    group_key: str
    group_by: AttributionGroupBy
    count: int
    win_rate: float | None = None
    average_return_pct: float | None = None
    median_return_pct: float | None = None
    total_pnl: float | None = None
    average_score: float | None = None
    average_confidence: float | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

class AttributionReport(BaseModel):
    attribution_id: str
    group_by: AttributionGroupBy
    buckets: list[AttributionBucket]
    source_run_ids: list[str] = Field(default_factory=list)
    source_journal_ids: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    disclaimer: str = "Attribution report is research-only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "attribution_id": self.attribution_id,
            "group_by": self.group_by.value,
            "buckets_count": len(self.buckets)
        }

class ResearchNote(BaseModel):
    note_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    title: str
    body: str
    related_run_ids: list[str] = Field(default_factory=list)
    related_symbols: list[str] = Field(default_factory=list)
    related_strategies: list[str] = Field(default_factory=list)
    tags: list[ResearchTag] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: str) -> str:
        if not v:
            return v
        lower_v = v.lower()
        forbidden_phrases = ["guaranteed profit", "sure thing", "investment advice", "buy now"]
        for phrase in forbidden_phrases:
            if phrase in lower_v:
                raise ValueError("Note contains unsafe financial claims.")
        return v

class ResearchQuery(BaseModel):
    run_types: list[ResearchRunType] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    strategies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    status: list[ResearchRunStatus] = Field(default_factory=list)
    start_date: datetime | None = None
    end_date: datetime | None = None
    limit: int = 100
    sort_desc: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Limit must be positive")
        return v
