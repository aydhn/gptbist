from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from bist_signal_bot.core.exceptions import KnowledgeValidationError


class KnowledgeSourceType(str, Enum):
    WHATIF_REPORT = "WHATIF_REPORT"
    RESEARCH_LEDGER = "RESEARCH_LEDGER"
    SIGNAL_LIFECYCLE = "SIGNAL_LIFECYCLE"
    REVIEW_INBOX = "REVIEW_INBOX"
    DECISION_JOURNAL = "DECISION_JOURNAL"
    REVIEW_THESIS = "REVIEW_THESIS"
    BACKTEST_RESULT = "BACKTEST_RESULT"
    OPTIMIZATION_RESULT = "OPTIMIZATION_RESULT"
    ENSEMBLE_RESULT = "ENSEMBLE_RESULT"
    PORTFOLIO_RESEARCH = "PORTFOLIO_RESEARCH"
    STRESS_TEST = "STRESS_TEST"
    DRIFT_MONITORING = "DRIFT_MONITORING"
    RESEARCH_LAB = "RESEARCH_LAB"
    REPORT = "REPORT"
    GOVERNANCE = "GOVERNANCE"
    RELEASE = "RELEASE"
    SCENARIO = "SCENARIO"
    MAINTENANCE = "MAINTENANCE"
    MANUAL_NOTE = "MANUAL_NOTE"
    UNKNOWN = "UNKNOWN"


class KnowledgeDocumentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    STALE = "STALE"
    DELETED = "DELETED"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"


class KnowledgeIndexStatus(str, Enum):
    READY = "READY"
    BUILDING = "BUILDING"
    PARTIAL = "PARTIAL"
    STALE = "STALE"
    FAILED = "FAILED"
    EMPTY = "EMPTY"
    UNKNOWN = "UNKNOWN"


class KnowledgeSearchMode(str, Enum):
    KEYWORD = "KEYWORD"
    BM25_LITE = "BM25_LITE"
    EMBEDDING = "EMBEDDING"
    HYBRID = "HYBRID"
    AUTO = "AUTO"


class KnowledgeEvidenceUse(str, Enum):
    REVIEW_CONTEXT = "REVIEW_CONTEXT"
    REPORT_CONTEXT = "REPORT_CONTEXT"
    RESEARCH_LAB_CONTEXT = "RESEARCH_LAB_CONTEXT"
    SIMILAR_CASE = "SIMILAR_CASE"
    AUDIT_CONTEXT = "AUDIT_CONTEXT"
    MANUAL_QUERY = "MANUAL_QUERY"
    UNKNOWN = "UNKNOWN"


class KnowledgeDocument(BaseModel):
    document_id: str
    source_type: KnowledgeSourceType
    source_ref: str | None = None
    symbol: str | None = None
    strategy_name: str | None = None
    title: str
    text: str
    created_at: datetime
    updated_at: datetime
    status: KnowledgeDocumentStatus = KnowledgeDocumentStatus.ACTIVE
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    disclaimer: str = "Knowledge document is research memory only. Not investment advice. No real order was sent."

    def model_post_init(self, __context: Any) -> None:
        if not self.title or not self.title.strip():
            raise KnowledgeValidationError("title cannot be empty")
        if not self.text or not self.text.strip():
            raise KnowledgeValidationError("text cannot be empty")

        if self.symbol:
            self.symbol = self.symbol.upper()


class KnowledgeChunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    token_estimate: int
    symbol: str | None = None
    strategy_name: str | None = None
    source_type: KnowledgeSourceType
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeIndexEntry(BaseModel):
    entry_id: str
    chunk_id: str
    document_id: str
    terms: dict[str, int]
    normalized_text: str
    embedding_vector: list[float] | None = None
    indexed_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeSearchQuery(BaseModel):
    query: str
    mode: KnowledgeSearchMode = KnowledgeSearchMode.AUTO
    symbols: list[str] = Field(default_factory=list)
    strategies: list[str] = Field(default_factory=list)
    source_types: list[KnowledgeSourceType] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    limit: int = 10
    include_archived: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if not self.query or not self.query.strip():
            raise KnowledgeValidationError("query cannot be empty")
        if self.limit <= 0:
            raise KnowledgeValidationError("limit must be positive")

        self.symbols = [sym.upper() for sym in self.symbols]


class KnowledgeSearchResultItem(BaseModel):
    rank: int
    document_id: str
    chunk_id: str | None = None
    source_type: KnowledgeSourceType
    source_ref: str | None = None
    title: str
    snippet: str
    score: float
    symbol: str | None = None
    strategy_name: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeSearchResult(BaseModel):
    query: KnowledgeSearchQuery
    mode_used: KnowledgeSearchMode
    status: KnowledgeIndexStatus
    items: list[KnowledgeSearchResultItem] = Field(default_factory=list)
    total_matches: int = 0
    elapsed_seconds: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Knowledge search result is research memory only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)


class SimilarCaseRequest(BaseModel):
    symbol: str | None = None
    strategy_name: str | None = None
    signal_payload: dict[str, Any] = Field(default_factory=dict)
    text_query: str | None = None
    lookback_days: int | None = None
    limit: int = 10
    metadata: dict[str, Any] = Field(default_factory=dict)


class SimilarCase(BaseModel):
    case_id: str
    document_id: str
    source_type: KnowledgeSourceType
    symbol: str | None = None
    strategy_name: str | None = None
    similarity_score: float
    title: str
    summary: str
    outcome_summary: str | None = None
    decision_summary: str | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CaseLibraryResult(BaseModel):
    request: SimilarCaseRequest
    cases: list[SimilarCase] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Similar cases are historical research context only. Past outcomes do not guarantee future results. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalystMemoryCard(BaseModel):
    memory_id: str
    symbol: str | None = None
    strategy_name: str | None = None
    title: str
    summary: str
    key_lessons: list[str] = Field(default_factory=list)
    repeated_patterns: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)
    last_seen_at: datetime | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    disclaimer: str = "Analyst memory is research-only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeIndexBuildRequest(BaseModel):
    source_types: list[KnowledgeSourceType] = Field(default_factory=list)
    rebuild: bool = False
    incremental: bool = True
    include_archived: bool = False
    use_embeddings: bool = False
    confirm_rebuild: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeIndexBuildResult(BaseModel):
    build_id: str
    request: KnowledgeIndexBuildRequest
    status: KnowledgeIndexStatus
    documents_seen: int = 0
    documents_indexed: int = 0
    chunks_created: int = 0
    entries_indexed: int = 0
    embeddings_created: int = 0
    skipped_documents: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    elapsed_seconds: float = 0.0
    output_files: dict[str, str] = Field(default_factory=dict)
    disclaimer: str = "Knowledge index build is operational research memory output only. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
