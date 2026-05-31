from typing import Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class LeaderboardStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    DEGRADED = "DEGRADED"
    FAIL = "FAIL"
    BLOCKED_RESEARCH = "BLOCKED_RESEARCH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"

class CandidateType(str, Enum):
    STRATEGY = "STRATEGY"
    MODEL = "MODEL"
    FEATURE_SET = "FEATURE_SET"
    SIGNAL_FAMILY = "SIGNAL_FAMILY"
    PORTFOLIO_RESEARCH = "PORTFOLIO_RESEARCH"
    CUSTOM = "CUSTOM"

class CandidateDecision(str, Enum):
    TOP_RESEARCH_CANDIDATE = "TOP_RESEARCH_CANDIDATE"
    WATCH_RESEARCH_CANDIDATE = "WATCH_RESEARCH_CANDIDATE"
    NEEDS_MORE_DATA = "NEEDS_MORE_DATA"
    REJECT_RESEARCH_CANDIDATE = "REJECT_RESEARCH_CANDIDATE"
    ESCALATE_REVIEW = "ESCALATE_REVIEW"
    BLOCKED_RESEARCH = "BLOCKED_RESEARCH"
    UNKNOWN = "UNKNOWN"

class BenchmarkCohortType(str, Enum):
    STRATEGY_COHORT = "STRATEGY_COHORT"
    MODEL_COHORT = "MODEL_COHORT"
    FEATURE_SET_COHORT = "FEATURE_SET_COHORT"
    MIXED_RESEARCH_COHORT = "MIXED_RESEARCH_COHORT"
    PORTFOLIO_RESEARCH_COHORT = "PORTFOLIO_RESEARCH_COHORT"
    CUSTOM = "CUSTOM"

class RankingMetricName(str, Enum):
    VALIDATION_SCORE = "VALIDATION_SCORE"
    CALIBRATION_SCORE = "CALIBRATION_SCORE"
    MONITORING_HEALTH = "MONITORING_HEALTH"
    ROBUSTNESS_SCORE = "ROBUSTNESS_SCORE"
    FEATURE_QUALITY = "FEATURE_QUALITY"
    MODEL_GOVERNANCE = "MODEL_GOVERNANCE"
    CONTEXT_SUPPORT = "CONTEXT_SUPPORT"
    REVIEW_BURDEN = "REVIEW_BURDEN"
    DATA_QUALITY = "DATA_QUALITY"
    RISK_ADJUSTED_SCORE = "RISK_ADJUSTED_SCORE"
    STABILITY_SCORE = "STABILITY_SCORE"
    CUSTOM = "CUSTOM"

class BenchmarkCohort(BaseModel):
    cohort_id: str
    cohort_type: BenchmarkCohortType
    name: str
    description: str
    candidate_type: CandidateType
    candidate_ids: list[str] = Field(default_factory=list)
    baseline_candidate_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    as_of: datetime = Field(default_factory=datetime.now)
    filters: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Benchmark cohort is local research comparison metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class CandidateMetric(BaseModel):
    metric_id: str
    candidate_type: CandidateType
    candidate_id: str
    metric_name: RankingMetricName
    value: float | None = None
    normalized_value: float | None = None
    weight: float = 1.0
    direction: str = "HIGHER_IS_BETTER"
    sample_count: int | None = None
    status: LeaderboardStatus = LeaderboardStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ResearchCandidate(BaseModel):
    candidate_id: str
    candidate_type: CandidateType
    name: str
    version: str | None = None
    owner_module: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    status: LeaderboardStatus = LeaderboardStatus.UNKNOWN
    metrics: list[CandidateMetric] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Research candidate is local research metadata only. It is not investment advice, recommendation, or order instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class CandidateScore(BaseModel):
    score_id: str
    candidate_id: str
    candidate_type: CandidateType
    as_of: datetime = Field(default_factory=datetime.now)
    raw_score: float | None = None
    adjusted_score: float | None = None
    rank_score: float | None = None
    metric_scores: dict[str, float | None] = Field(default_factory=dict)
    penalties: dict[str, float] = Field(default_factory=dict)
    positive_contributors: list[str] = Field(default_factory=list)
    negative_contributors: list[str] = Field(default_factory=list)
    status: LeaderboardStatus = LeaderboardStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Candidate score is research-only ranking metadata. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class LeaderboardEntry(BaseModel):
    entry_id: str
    leaderboard_id: str
    rank: int | None = None
    candidate: ResearchCandidate
    score: CandidateScore
    decision: CandidateDecision = CandidateDecision.UNKNOWN
    review_required: bool = False
    key_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class ResearchLeaderboard(BaseModel):
    leaderboard_id: str
    cohort_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    as_of: datetime = Field(default_factory=datetime.now)
    entries: list[LeaderboardEntry] = Field(default_factory=list)
    status: LeaderboardStatus = LeaderboardStatus.UNKNOWN
    top_candidate_id: str | None = None
    watch_count: int = 0
    blocked_count: int = 0
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Research leaderboard is local comparison output only. It is not investment advice, portfolio advice, or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class CandidateComparison(BaseModel):
    comparison_id: str
    candidate_a_id: str
    candidate_b_id: str
    candidate_type: CandidateType
    as_of: datetime = Field(default_factory=datetime.now)
    metric_deltas: dict[str, float | None] = Field(default_factory=dict)
    winner_candidate_id: str | None = None
    decision: CandidateDecision = CandidateDecision.UNKNOWN
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Candidate comparison is research-only metadata. It is not investment advice or live deployment approval. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class SelectionPolicy(BaseModel):
    policy_id: str
    name: str
    version: str
    candidate_type: CandidateType
    min_rank_score: float | None = None
    min_sample_count: int | None = None
    max_review_burden: float | None = None
    block_on_leakage: bool = True
    block_on_governance_fail: bool = True
    block_on_data_quality_fail: bool = False
    require_monitoring_pass: bool = False
    require_calibration_pass: bool = False
    require_model_card: bool = False
    weights: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Selection policy is local research governance metadata only. It is not trade automation policy or investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class CandidateSelectionResult(BaseModel):
    selection_id: str
    policy_id: str
    leaderboard_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    selected_candidate_ids: list[str] = Field(default_factory=list)
    rejected_candidate_ids: list[str] = Field(default_factory=list)
    watch_candidate_ids: list[str] = Field(default_factory=list)
    review_required_ids: list[str] = Field(default_factory=list)
    blocking_reasons: dict[str, list[str]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Candidate selection result is research-only. It is not investment advice, portfolio construction instruction, or order instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class LeaderboardReport(BaseModel):
    report_id: str
    generated_at: datetime = Field(default_factory=datetime.now)
    cohorts: list[BenchmarkCohort] = Field(default_factory=list)
    candidates: list[ResearchCandidate] = Field(default_factory=list)
    leaderboards: list[ResearchLeaderboard] = Field(default_factory=list)
    comparisons: list[CandidateComparison] = Field(default_factory=list)
    policies: list[SelectionPolicy] = Field(default_factory=list)
    selections: list[CandidateSelectionResult] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Leaderboard report is local research comparison reporting only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
