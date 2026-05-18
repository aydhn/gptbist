from enum import Enum
from typing import Any, List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from bist_signal_bot.signals.models import SignalCandidate
from bist_signal_bot.risk.models import RiskDecision
from bist_signal_bot.portfolio.models import PortfolioRiskDecision

class ScanUniverseMode(str, Enum):
    SYMBOLS = "SYMBOLS"
    WATCHLIST = "WATCHLIST"
    GROUP = "GROUP"
    ALL = "ALL"
    CUSTOM = "CUSTOM"

class ScanStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    EMPTY = "EMPTY"

class ScanCandidateStatus(str, Enum):
    PASSED = "PASSED"
    FILTERED = "FILTERED"
    REJECTED = "REJECTED"
    ERROR = "ERROR"
    WATCH_ONLY = "WATCH_ONLY"

class ScanSortKey(str, Enum):
    FINAL_SCORE = "FINAL_SCORE"
    SIGNAL_SCORE = "SIGNAL_SCORE"
    CONFIDENCE = "CONFIDENCE"
    RISK_REWARD = "RISK_REWARD"
    LIQUIDITY = "LIQUIDITY"
    VOLUME_ACTIVITY = "VOLUME_ACTIVITY"
    MOMENTUM = "MOMENTUM"
    TREND = "TREND"
    LOW_COST = "LOW_COST"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    ML_SCORE = "ML_SCORE"
    ML_PROBABILITY = "ML_PROBABILITY"

class ScanRequest(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    strategy_name: str
    universe_mode: ScanUniverseMode
    symbols: List[str] = Field(default_factory=list)
    watchlist_name: Optional[str] = None
    group_name: Optional[str] = None
    source: str = "mock"
    timeframe: str = "1d"
    rows: Optional[int] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    use_trade_risk: bool = True
    use_portfolio_risk: bool = True
    use_paper: bool = False
    top_n: int = 10
    min_signal_score: float = 50.0
    min_confidence: float = 40.0
    min_final_score: float = 50.0
    sort_key: ScanSortKey = ScanSortKey.FINAL_SCORE
    descending: bool = True
    continue_on_error: bool = True
    save_report: bool = False
    send_telegram: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SymbolScanIssue(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    symbol: Optional[str] = None
    stage: str
    message: str
    severity: str = "ERROR"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SymbolScanResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    symbol: str
    status: ScanCandidateStatus
    signal: Optional[SignalCandidate] = None
    risk_decision: Optional[RiskDecision] = None
    portfolio_status: Optional[str] = None
    rank_score: Optional[float] = None
    rank: Optional[int] = None
    reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    data_provider: Optional[str] = None
    data_lineage_source_id: Optional[str] = None
    data_freshness_age_hours: Optional[float] = None
    data_quality_warnings: List[str] = Field(default_factory=list)
    issues: List[SymbolScanIssue] = Field(default_factory=list)
    elapsed_seconds: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "status": self.status.value,
            "signal_intent": self.signal.direction.value if self.signal else None,
            "signal_score": self.signal.score if self.signal else None,
            "final_score": self.risk_decision.final_score if self.risk_decision else None,
            "portfolio_status": self.portfolio_status,
            "rank": self.rank,
            "rank_score": self.rank_score,
            "elapsed_seconds": self.elapsed_seconds
        }

class ScanRankingItem(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    symbol: str
    rank_score: float
    rank: int
    signal_score: Optional[float] = None
    confidence: Optional[float] = None
    final_score: Optional[float] = None
    risk_reward: Optional[float] = None
    liquidity_score: Optional[float] = None
    volatility_score: Optional[float] = None
    cost_bps: Optional[float] = None
    direction: Optional[str] = None
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ScanReport(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    request: ScanRequest
    status: ScanStatus = ScanStatus.EMPTY
    total_symbols: int = 0
    processed_symbols: int = 0
    passed_count: int = 0
    filtered_count: int = 0
    rejected_count: int = 0
    error_count: int = 0
    watch_only_count: int = 0
    results: List[SymbolScanResult] = Field(default_factory=list)
    rankings: List[ScanRankingItem] = Field(default_factory=list)
    portfolio_decision: Optional[PortfolioRiskDecision] = None
    paper_result_summary: Optional[Dict[str, Any]] = None
    issues: List[SymbolScanIssue] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime = Field(default_factory=datetime.utcnow)
    elapsed_seconds: float = 0.0
    output_files: Dict[str, str] = Field(default_factory=dict)
    disclaimer: str = "Signal scan research output only. Not investment advice. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "strategy": self.request.strategy_name,
            "total_symbols": self.total_symbols,
            "processed": self.processed_symbols,
            "passed": self.passed_count,
            "filtered": self.filtered_count,
            "rejected": self.rejected_count,
            "error": self.error_count,
            "elapsed_seconds": self.elapsed_seconds,
            "output_files": self.output_files
        }

    def top_candidates(self, n: Optional[int] = None) -> List[SymbolScanResult]:
        passed = [r for r in self.results if r.status == ScanCandidateStatus.PASSED]
        passed.sort(key=lambda x: x.rank if x.rank is not None else 999999)
        if n is not None:
            return passed[:n]
        return passed

    def safe_public_dict(self) -> Dict[str, Any]:
        return self.summary()
