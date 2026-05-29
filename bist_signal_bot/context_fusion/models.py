from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ContextStatus(str, Enum):
    STRONG_SUPPORT = "STRONG_SUPPORT"
    SUPPORT = "SUPPORT"
    NEUTRAL = "NEUTRAL"
    PRESSURE = "PRESSURE"
    HIGH_PRESSURE = "HIGH_PRESSURE"
    CONFLICTED = "CONFLICTED"
    WATCH = "WATCH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    STALE = "STALE"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class ContextLayer(str, Enum):
    TECHNICAL_SIGNAL = "TECHNICAL_SIGNAL"
    ML = "ML"
    ENSEMBLE = "ENSEMBLE"
    RISK = "RISK"
    EXECUTION = "EXECUTION"
    CALIBRATION = "CALIBRATION"
    VALIDATION = "VALIDATION"
    MONTE_CARLO = "MONTE_CARLO"
    STRATEGY_REGISTRY = "STRATEGY_REGISTRY"
    EVENT_RISK = "EVENT_RISK"
    DISCLOSURE = "DISCLOSURE"
    FINANCIALS = "FINANCIALS"
    VALUATION = "VALUATION"
    FACTORS = "FACTORS"
    BREADTH = "BREADTH"
    MACRO = "MACRO"
    PORTFOLIO = "PORTFOLIO"
    KNOWLEDGE = "KNOWLEDGE"
    REVIEW = "REVIEW"
    CUSTOM = "CUSTOM"


class ContextDirection(str, Enum):
    SUPPORTIVE = "SUPPORTIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"
    MIXED = "MIXED"
    BLOCKING_RESEARCH = "BLOCKING_RESEARCH"
    UNKNOWN = "UNKNOWN"


class ContextImportance(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ConflictType(str, Enum):
    HIGH_SCORE_HIGH_RISK = "HIGH_SCORE_HIGH_RISK"
    TECHNICAL_VS_MACRO = "TECHNICAL_VS_MACRO"
    TECHNICAL_VS_BREADTH = "TECHNICAL_VS_BREADTH"
    TECHNICAL_VS_EVENT = "TECHNICAL_VS_EVENT"
    TECHNICAL_VS_VALUATION = "TECHNICAL_VS_VALUATION"
    TECHNICAL_VS_FACTOR = "TECHNICAL_VS_FACTOR"
    ML_VS_STRATEGY = "ML_VS_STRATEGY"
    ENSEMBLE_DISAGREEMENT = "ENSEMBLE_DISAGREEMENT"
    CALIBRATION_MISMATCH = "CALIBRATION_MISMATCH"
    VALIDATION_OVERFIT_WARNING = "VALIDATION_OVERFIT_WARNING"
    LIQUIDITY_COST_CONFLICT = "LIQUIDITY_COST_CONFLICT"
    PORTFOLIO_CONCENTRATION_CONFLICT = "PORTFOLIO_CONCENTRATION_CONFLICT"
    STALE_CONTEXT_CONFLICT = "STALE_CONTEXT_CONFLICT"
    MISSING_EVIDENCE_CONFLICT = "MISSING_EVIDENCE_CONFLICT"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"


class EvidenceGapType(str, Enum):
    MISSING_DATA = "MISSING_DATA"
    STALE_DATA = "STALE_DATA"
    LOW_SAMPLE_SIZE = "LOW_SAMPLE_SIZE"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    UNAVAILABLE_CONTEXT = "UNAVAILABLE_CONTEXT"
    FAILED_COLLECTOR = "FAILED_COLLECTOR"
    LOW_CONFIDENCE_SOURCE = "LOW_CONFIDENCE_SOURCE"
    CONFLICTING_SOURCES = "CONFLICTING_SOURCES"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"


class ResearchGraphNodeType(str, Enum):
    SYMBOL = "SYMBOL"
    SIGNAL = "SIGNAL"
    STRATEGY = "STRATEGY"
    CONTEXT_LAYER = "CONTEXT_LAYER"
    EVENT = "EVENT"
    DISCLOSURE = "DISCLOSURE"
    FINANCIAL_STATEMENT = "FINANCIAL_STATEMENT"
    VALUATION = "VALUATION"
    FACTOR = "FACTOR"
    BREADTH_REGIME = "BREADTH_REGIME"
    MACRO_REGIME = "MACRO_REGIME"
    PORTFOLIO = "PORTFOLIO"
    REVIEW_ITEM = "REVIEW_ITEM"
    EVIDENCE = "EVIDENCE"
    CUSTOM = "CUSTOM"


class ContextSourceRef(BaseModel):
    source_id: str
    layer: ContextLayer
    object_type: str
    object_id: Optional[str] = None
    source_path: Optional[str] = None
    freshness_timestamp: Optional[datetime] = None
    confidence: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("confidence")
    def clamp_confidence(cls, v):
        if v is not None:
            return max(0.0, min(100.0, v))
        return v

    @field_validator("source_path")
    def validate_source_path(cls, v):
        if v and any(s in v.lower() for s in ["secret", "token", "password", "key", ".env"]):
            return "[REDACTED]"
        return v


class ContextSignal(BaseModel):
    context_id: str
    layer: ContextLayer
    symbol: Optional[str] = None
    strategy_name: Optional[str] = None
    signal_id: Optional[str] = None
    as_of: datetime
    title: str
    value: Any = None
    score: Optional[float] = None
    normalized_score: Optional[float] = None
    direction: ContextDirection
    status: ContextStatus
    importance: ContextImportance
    message: str
    source_ref: Optional[ContextSourceRef] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol")
    def normalize_symbol(cls, v):
        if v is not None:
            return v.upper()
        return v

    @field_validator("score", "normalized_score")
    def clamp_scores(cls, v):
        if v is not None:
            return max(0.0, min(100.0, v))
        return v

    @field_validator("message")
    def validate_safe_message(cls, v):
        unsafe_words = ["garanti", "kesin", "risksiz", "tavsiye", "hedef fiyat"]
        msg = v
        for w in unsafe_words:
            # simple replacement ignores case but preserves original string structure better,
            # let's just do a naive case insensitive replace
            import re
            msg = re.sub(f"(?i){w}", "[REDACTED_UNSAFE_CLAIM]", msg)
        return msg

class ContextLayerSummary(BaseModel):
    summary_id: str
    layer: ContextLayer
    symbol: Optional[str] = None
    strategy_name: Optional[str] = None
    as_of: datetime
    signals: List[ContextSignal]
    layer_score: Optional[float] = None
    layer_status: ContextStatus
    dominant_direction: ContextDirection
    key_points: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContextConflict(BaseModel):
    conflict_id: str
    conflict_type: ConflictType
    symbol: Optional[str] = None
    signal_id: Optional[str] = None
    involved_layers: List[ContextLayer] = Field(default_factory=list)
    severity: ContextImportance
    score_impact: Optional[float] = None
    message: str
    suggested_review_reason: Optional[str] = None
    evidence_refs: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Context conflict is research-only metadata. It is not investment advice or an order instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceGap(BaseModel):
    gap_id: str
    gap_type: EvidenceGapType
    layer: ContextLayer
    symbol: Optional[str] = None
    object_id: Optional[str] = None
    severity: ContextImportance
    message: str
    recommended_data_action: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResearchGraphNode(BaseModel):
    node_id: str
    node_type: ResearchGraphNodeType
    label: str
    object_id: Optional[str] = None
    symbol: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResearchGraphEdge(BaseModel):
    edge_id: str
    from_node_id: str
    to_node_id: str
    relationship: str
    weight: Optional[float] = None
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResearchGraph(BaseModel):
    graph_id: str
    created_at: datetime
    symbol: Optional[str] = None
    signal_id: Optional[str] = None
    nodes: List[ResearchGraphNode] = Field(default_factory=list)
    edges: List[ResearchGraphEdge] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Research graph is local research metadata only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CompositeResearchScore(BaseModel):
    score_id: str
    symbol: Optional[str] = None
    signal_id: Optional[str] = None
    strategy_name: Optional[str] = None
    as_of: datetime
    base_score: Optional[float] = None
    adjusted_score: Optional[float] = None
    layer_scores: Dict[str, Optional[float]] = Field(default_factory=dict)
    layer_weights: Dict[str, float] = Field(default_factory=dict)
    positive_contributors: List[str] = Field(default_factory=list)
    negative_contributors: List[str] = Field(default_factory=list)
    conflict_penalty: Optional[float] = None
    evidence_gap_penalty: Optional[float] = None
    final_status: ContextStatus
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Composite research score is research-only. It is not investment advice, a recommendation, or an order instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UnifiedContextSnapshot(BaseModel):
    snapshot_id: str
    created_at: datetime
    symbol: str
    strategy_name: Optional[str] = None
    signal_id: Optional[str] = None
    as_of: datetime
    layer_summaries: List[ContextLayerSummary] = Field(default_factory=list)
    context_signals: List[ContextSignal] = Field(default_factory=list)
    conflicts: List[ContextConflict] = Field(default_factory=list)
    evidence_gaps: List[EvidenceGap] = Field(default_factory=list)
    research_graph: Optional[ResearchGraph] = None
    composite_score: Optional[CompositeResearchScore] = None
    key_supports: List[str] = Field(default_factory=list)
    key_pressures: List[str] = Field(default_factory=list)
    required_reviews: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Unified context snapshot is research-only. It is not investment advice, portfolio advice, or an order instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "symbol": self.symbol,
            "signal_id": self.signal_id,
            "as_of": self.as_of.isoformat() if self.as_of else None,
            "composite_score": self.composite_score.adjusted_score if self.composite_score else None,
            "final_status": self.composite_score.final_status.value if self.composite_score else ContextStatus.UNKNOWN.value,
            "conflict_count": len(self.conflicts),
            "evidence_gap_count": len(self.evidence_gaps),
            "key_supports": self.key_supports,
            "key_pressures": self.key_pressures
        }

    def safe_public_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        data.pop("metadata", None)
        return data


class ContextFusionReport(BaseModel):
    report_id: str
    generated_at: datetime
    snapshots: List[UnifiedContextSnapshot] = Field(default_factory=list)
    conflicts: List[ContextConflict] = Field(default_factory=list)
    evidence_gaps: List[EvidenceGap] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Context fusion report is research-only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)
