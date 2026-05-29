from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional

class ReviewCaseStatus(Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    NEEDS_DATA = "NEEDS_DATA"
    WAITING_SIGNOFF = "WAITING_SIGNOFF"
    WATCH = "WATCH"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class ReviewCasePriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class ReviewCaseType(Enum):
    SIGNAL_REVIEW = "SIGNAL_REVIEW"
    SYMBOL_REVIEW = "SYMBOL_REVIEW"
    STRATEGY_REVIEW = "STRATEGY_REVIEW"
    PORTFOLIO_REVIEW = "PORTFOLIO_REVIEW"
    CONTEXT_CONFLICT_REVIEW = "CONTEXT_CONFLICT_REVIEW"
    EVENT_RISK_REVIEW = "EVENT_RISK_REVIEW"
    DISCLOSURE_RISK_REVIEW = "DISCLOSURE_RISK_REVIEW"
    CALIBRATION_REVIEW = "CALIBRATION_REVIEW"
    VALIDATION_REVIEW = "VALIDATION_REVIEW"
    DATA_QUALITY_REVIEW = "DATA_QUALITY_REVIEW"
    CUSTOM = "CUSTOM"

class ReviewDisposition(Enum):
    RESEARCH_SUPPORT = "RESEARCH_SUPPORT"
    RESEARCH_WATCH = "RESEARCH_WATCH"
    RESEARCH_REJECT = "RESEARCH_REJECT"
    NEEDS_MORE_DATA = "NEEDS_MORE_DATA"
    DEFER = "DEFER"
    ESCALATE = "ESCALATE"
    NO_ACTION = "NO_ACTION"
    UNKNOWN = "UNKNOWN"

class ReviewPlaybookType(Enum):
    HIGH_SCORE_HIGH_RISK = "HIGH_SCORE_HIGH_RISK"
    MACRO_PRESSURE = "MACRO_PRESSURE"
    BREADTH_DIVERGENCE = "BREADTH_DIVERGENCE"
    EVENT_BLACKOUT = "EVENT_BLACKOUT"
    DISCLOSURE_HIGH_SEVERITY = "DISCLOSURE_HIGH_SEVERITY"
    VALUATION_VALUE_TRAP = "VALUATION_VALUE_TRAP"
    FACTOR_CROWDING = "FACTOR_CROWDING"
    LIQUIDITY_COST = "LIQUIDITY_COST"
    CALIBRATION_LOW_RELIABILITY = "CALIBRATION_LOW_RELIABILITY"
    VALIDATION_OVERFIT = "VALIDATION_OVERFIT"
    PORTFOLIO_CONCENTRATION = "PORTFOLIO_CONCENTRATION"
    MISSING_DATA = "MISSING_DATA"
    STANDARD_SIGNAL_REVIEW = "STANDARD_SIGNAL_REVIEW"
    CUSTOM = "CUSTOM"

class ChecklistItemStatus(Enum):
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NEEDS_DATA = "NEEDS_DATA"
    UNKNOWN = "UNKNOWN"

class SignoffStatus(Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    REQUIRED = "REQUIRED"
    REQUESTED = "REQUESTED"
    APPROVED_RESEARCH = "APPROVED_RESEARCH"
    REJECTED_RESEARCH = "REJECTED_RESEARCH"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


@dataclass
class ReviewPlaybook:
    playbook_id: str
    playbook_type: ReviewPlaybookType
    name: str
    description: str
    triggers: list[str] = field(default_factory=list)
    checklist_templates: list[str] = field(default_factory=list)
    required_context_layers: list[str] = field(default_factory=list)
    required_signoff_priority: Optional[ReviewCasePriority] = None
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Review playbook is research-only workflow metadata. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ReviewChecklistItem:
    item_id: str
    case_id: str
    title: str
    description: str
    status: ChecklistItemStatus = ChecklistItemStatus.PENDING
    required: bool = False
    evidence_refs: list[str] = field(default_factory=list)
    analyst_note: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ReviewCase:
    case_id: str
    case_type: ReviewCaseType
    status: ReviewCaseStatus
    priority: ReviewCasePriority
    title: str
    summary: str
    symbol: Optional[str] = None
    strategy_name: Optional[str] = None
    signal_id: Optional[str] = None
    snapshot_id: Optional[str] = None
    playbook_ids: list[str] = field(default_factory=list)
    required_reviews: list[str] = field(default_factory=list)
    checklist: list[ReviewChecklistItem] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    evidence_gaps: list[str] = field(default_factory=list)
    disposition: ReviewDisposition = ReviewDisposition.UNKNOWN
    signoff_status: SignoffStatus = SignoffStatus.NOT_REQUIRED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: Optional[datetime] = None
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Review case is research-only. It is not investment advice, trade approval, or an order instruction. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.title:
            raise ValueError("title cannot be empty")
        if self.symbol:
            self.symbol = self.symbol.upper()
        if self.closed_at and self.status not in (ReviewCaseStatus.CLOSED, ReviewCaseStatus.CANCELLED, ReviewCaseStatus.ARCHIVED):
            raise ValueError(f"closed_at is set but status is {self.status.name}")

@dataclass
class DecisionJournalEntry:
    entry_id: str
    case_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    actor: Optional[str] = None
    entry_type: str = "NOTE"
    previous_status: Optional[ReviewCaseStatus] = None
    new_status: Optional[ReviewCaseStatus] = None
    disposition: Optional[ReviewDisposition] = None
    note: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    correction_of: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Decision journal entry is research-only and append-only. It is not trade approval or investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ReviewSignoffRequest:
    signoff_id: str
    case_id: str
    reason: str
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    requested_by: Optional[str] = None
    requested_role: Optional[str] = None
    status: SignoffStatus = SignoffStatus.REQUESTED
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    expires_at: Optional[datetime] = None
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Review sign-off is research governance metadata only. It is not a trading approval. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ReviewDataAction:
    action_id: str
    action_type: str
    description: str
    status: str = "PENDING"
    priority: ReviewCasePriority = ReviewCasePriority.MEDIUM
    case_id: Optional[str] = None
    layer: Optional[str] = None
    symbol: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    evidence_gap_id: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ReviewPattern:
    pattern_id: str
    pattern_type: str
    count: int
    message: str
    severity: ReviewCasePriority = ReviewCasePriority.MEDIUM
    symbol: Optional[str] = None
    strategy_name: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    related_case_ids: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ReviewWorkflowReport:
    report_id: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    cases: list[ReviewCase] = field(default_factory=list)
    journal_entries: list[DecisionJournalEntry] = field(default_factory=list)
    signoffs: list[ReviewSignoffRequest] = field(default_factory=list)
    data_actions: list[ReviewDataAction] = field(default_factory=list)
    patterns: list[ReviewPattern] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Review workflow report is research-only. It is not investment advice, portfolio advice, or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)
