from typing import Any, List, Optional
import uuid
from loguru import logger

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio_construction.models import PortfolioCandidate, PortfolioConstructionRequest

class PortfolioCandidateBuilder:
    def __init__(self, settings: Settings, store=None):
        self.settings = settings
        self.store = store

    def build_candidates(self, request: PortfolioConstructionRequest) -> List[PortfolioCandidate]:
        candidates = []
        for symbol in request.symbols:
            candidate = PortfolioCandidate(
                candidate_id=f"cand_{uuid.uuid4().hex[:8]}",
                symbol=symbol,
            )
            candidate = self.score_candidate(candidate)
            candidates.append(candidate)

        filtered = self.filter_candidates(candidates, request)
        return self.rank_candidates(filtered)

    def candidate_from_signal(self, signal_payload: dict[str, Any]) -> PortfolioCandidate:
        candidate = PortfolioCandidate(
            candidate_id=f"cand_{uuid.uuid4().hex[:8]}",
            symbol=signal_payload.get("symbol", "UNKNOWN"),
            strategy_name=signal_payload.get("strategy_name"),
            signal_id=signal_payload.get("signal_id"),
            calibrated_confidence=signal_payload.get("calibrated_confidence"),
            raw_confidence=signal_payload.get("raw_confidence"),
        )
        return candidate

    def score_candidate(self, candidate: PortfolioCandidate) -> PortfolioCandidate:
        candidate.validation_score = 80.0
        candidate.monte_carlo_score = 75.0

        base_score = candidate.calibrated_confidence or candidate.raw_confidence or 50.0
        candidate.final_candidate_score = (base_score + (candidate.validation_score or 50) + (candidate.monte_carlo_score or 50)) / 3.0
        return candidate

    def filter_candidates(self, candidates: List[PortfolioCandidate], request: PortfolioConstructionRequest) -> List[PortfolioCandidate]:
        filtered = []
        for c in candidates:
            if c.metadata.get("is_blocked", False):
                continue
            if c.metadata.get("is_inactive", False):
                continue
            filtered.append(c)
        return filtered

    def rank_candidates(self, candidates: List[PortfolioCandidate], limit: Optional[int] = None) -> List[PortfolioCandidate]:
        ranked = sorted(candidates, key=lambda c: c.final_candidate_score or 0.0, reverse=True)
        if limit is not None:
            return ranked[:limit]
        return ranked
