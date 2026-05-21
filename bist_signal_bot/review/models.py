from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ReviewItemSource(str, Enum):
    SCANNER = "SCANNER"
    ENSEMBLE = "ENSEMBLE"
    SIGNAL_LIFECYCLE = "SIGNAL_LIFECYCLE"
    WATCHLIST = "WATCHLIST"
    PORTFOLIO_RESEARCH = "PORTFOLIO_RESEARCH"
    STRESS_TEST = "STRESS_TEST"
    DRIFT_MONITORING = "DRIFT_MONITORING"
    ADAPTIVE = "ADAPTIVE"
    RESEARCH_LAB = "RESEARCH_LAB"
    MANUAL = "MANUAL"
    UNKNOWN = "UNKNOWN"

class ReviewItemStatus(str, Enum):
    NEW = "NEW"
    IN_REVIEW = "IN_REVIEW"
    WAITING_DATA = "WAITING_DATA"
    WAITING_FOLLOWUP = "WAITING_FOLLOWUP"
    APPROVED_RESEARCH = "APPROVED_RESEARCH"
    WATCH_ONLY = "WATCH_ONLY"
    REJECTED_RESEARCH = "REJECTED_RESEARCH"
    ARCHIVED = "ARCHIVED"
    EXPIRED = "EXPIRED"
    ERROR = "ERROR"

class ReviewDecisionType(str, Enum):
    APPROVE_RESEARCH = "APPROVE_RESEARCH"
    WATCH_ONLY = "WATCH_ONLY"
    REJECT_RESEARCH = "REJECT_RESEARCH"
    NEEDS_MORE_DATA = "NEEDS_MORE_DATA"
    WAIT_FOR_FOLLOWUP = "WAIT_FOR_FOLLOWUP"
    ARCHIVE = "ARCHIVE"
    REOPEN = "REOPEN"
    NO_DECISION = "NO_DECISION"

class ReviewPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"
    UNKNOWN = "UNKNOWN"

class ChecklistItemStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"
    UNKNOWN = "UNKNOWN"

class ThesisStrength(str, Enum):
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    CONFLICTED = "CONFLICTED"
    UNKNOWN = "UNKNOWN"

class ReviewEvidenceType(str, Enum):
    TECHNICAL = "TECHNICAL"
    FUNDAMENTAL = "FUNDAMENTAL"
    BREADTH = "BREADTH"
    RELATIVE_STRENGTH = "RELATIVE_STRENGTH"
    REGIME = "REGIME"
    RISK = "RISK"
    ML = "ML"
    ENSEMBLE = "ENSEMBLE"
    SIGNAL_LIFECYCLE = "SIGNAL_LIFECYCLE"
    PORTFOLIO = "PORTFOLIO"
    STRESS = "STRESS"
    DRIFT = "DRIFT"
    GOVERNANCE = "GOVERNANCE"
    MANUAL_NOTE = "MANUAL_NOTE"
    UNKNOWN = "UNKNOWN"

class ReviewChecklistItem(BaseModel):
    item_id: str
    name: str
    status: ChecklistItemStatus = ChecklistItemStatus.UNKNOWN
    message: str = ""
    required: bool = False
    evidence_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReviewChecklist(BaseModel):
    checklist_id: str
    item_id: str
    created_at: datetime
    updated_at: datetime
    items: List[ReviewChecklistItem] = Field(default_factory=list)
    pass_count: int = 0
    warn_count: int = 0
    fail_count: int = 0
    required_fail_count: int = 0
    overall_status: ChecklistItemStatus = ChecklistItemStatus.UNKNOWN
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        return {
            "checklist_id": self.checklist_id,
            "overall_status": self.overall_status.value,
            "pass_count": self.pass_count,
            "warn_count": self.warn_count,
            "fail_count": self.fail_count,
            "required_fail_count": self.required_fail_count,
        }

class ReviewThesis(BaseModel):
    thesis_id: str
    item_id: str
    symbol: str
    created_at: datetime
    updated_at: datetime
    main_thesis: str
    counter_thesis: str = ""
    invalidation_points: List[str] = Field(default_factory=list)
    key_risks: List[str] = Field(default_factory=list)
    expected_followup: Optional[str] = None
    thesis_strength: ThesisStrength = ThesisStrength.UNKNOWN
    evidence_refs: List[str] = Field(default_factory=list)
    disclaimer: str = "Review thesis is research-only. Not investment advice. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReviewEvidence(BaseModel):
    evidence_id: str
    item_id: str
    evidence_type: ReviewEvidenceType
    source_ref: Optional[str] = None
    title: str
    summary: str
    score: Optional[float] = None
    status: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReviewDecision(BaseModel):
    decision_id: str
    item_id: str
    decision_type: ReviewDecisionType
    previous_status: Optional[ReviewItemStatus] = None
    new_status: ReviewItemStatus
    decided_at: datetime
    decided_by: Optional[str] = None
    reason: str
    confidence: Optional[float] = None
    checklist_id: Optional[str] = None
    thesis_id: Optional[str] = None
    followup_at: Optional[datetime] = None
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Review decision is research-only. It is not an order instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReviewItem(BaseModel):
    item_id: str
    source: ReviewItemSource
    source_ref: Optional[str] = None
    symbol: str
    strategy_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    status: ReviewItemStatus = ReviewItemStatus.NEW
    priority: ReviewPriority = ReviewPriority.NORMAL
    title: str
    summary: str
    score: Optional[float] = None
    confidence: Optional[float] = None
    consensus_score: Optional[float] = None
    risk_status: Optional[str] = None
    regime_status: Optional[str] = None
    breadth_status: Optional[str] = None
    stress_rating: Optional[str] = None
    drift_status: Optional[str] = None
    checklist_id: Optional[str] = None
    thesis_id: Optional[str] = None
    latest_decision_id: Optional[str] = None
    followup_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = "Review item is research-only. Not investment advice. No real order was sent."

    def summary_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "title": self.title,
            "score": self.score,
        }

    def summary(self) -> Dict[str, Any]:
        return self.summary_dict()

    def safe_public_dict(self) -> Dict[str, Any]:
        d = self.model_dump()
        d["metadata"] = {}
        return d

class DecisionJournalEntry(BaseModel):
    journal_id: str
    item_id: str
    symbol: str
    strategy_name: Optional[str] = None
    decision_id: str
    created_at: datetime
    decision_type: ReviewDecisionType
    status_after_decision: ReviewItemStatus
    thesis_summary: Optional[str] = None
    outcome_ref: Optional[str] = None
    lessons: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    disclaimer: str = "Decision journal entry is research-only. Past decisions do not guarantee future results. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReviewInboxSummary(BaseModel):
    total_items: int = 0
    new_count: int = 0
    in_review_count: int = 0
    approved_research_count: int = 0
    watch_only_count: int = 0
    rejected_count: int = 0
    waiting_followup_count: int = 0
    expired_count: int = 0
    high_priority_count: int = 0
    generated_at: datetime
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
