from typing import List, Optional

from bist_signal_bot.portfolio_construction.models import (
    PortfolioConstructionResult, PortfolioCandidate, PortfolioConstraintViolation,
    ConstraintSeverity, PortfolioConstructionStatus, RiskBudgetItem
)
from bist_signal_bot.config.settings import Settings

class PortfolioConstructionScorer:
    def __init__(self, settings: Settings):
        self.settings = settings

    def score_portfolio(self, result: PortfolioConstructionResult) -> Optional[float]:
        c_score = self.score_candidates(result.candidates) or 50.0
        d_score = result.diversification_score or 50.0
        constraint_penalty = (100.0 - (self.score_constraints(result.violations) or 100.0))
        cost_penalty = (100.0 - (self.score_execution_cost(result.estimated_total_cost_bps) or 100.0))

        score = (c_score * 0.4) + (d_score * 0.6) - constraint_penalty - cost_penalty
        return max(0.0, min(100.0, score))

    def score_candidates(self, candidates: List[PortfolioCandidate]) -> Optional[float]:
        if not candidates:
            return None
        scores = [c.final_candidate_score for c in candidates if c.final_candidate_score is not None]
        if not scores:
            return None
        return sum(scores) / len(scores)

    def score_constraints(self, violations: List[PortfolioConstraintViolation]) -> Optional[float]:
        if not violations:
            return 100.0

        score = 100.0
        for v in violations:
            if v.severity == ConstraintSeverity.CRITICAL:
                score -= 30.0
            elif v.severity == ConstraintSeverity.HIGH:
                score -= 15.0
            elif v.severity == ConstraintSeverity.MEDIUM:
                score -= 5.0
        return max(0.0, score)

    def score_execution_cost(self, estimated_total_cost_bps: Optional[float]) -> Optional[float]:
        if estimated_total_cost_bps is None:
            return 100.0
        if estimated_total_cost_bps > self.settings.PORTFOLIO_MAX_COST_DRAG_BPS:
            return max(0.0, 100.0 - (estimated_total_cost_bps - self.settings.PORTFOLIO_MAX_COST_DRAG_BPS))
        return 100.0

    def score_risk_budget(self, risk_budget: List[RiskBudgetItem]) -> Optional[float]:
        return 100.0

    def derive_status(self, score: Optional[float], violations: List[PortfolioConstraintViolation], warnings: List[str]) -> PortfolioConstructionStatus:
        has_critical = any(v.severity == ConstraintSeverity.CRITICAL for v in violations)

        if score is None:
            return PortfolioConstructionStatus.INSUFFICIENT_DATA

        if has_critical or score < 40.0:
            return PortfolioConstructionStatus.FAIL
        elif score < 60.0 or violations or warnings:
            return PortfolioConstructionStatus.WATCH
        return PortfolioConstructionStatus.PASS
