from typing import Any
from bist_signal_bot.portfolio_research.models import (
    ResearchPortfolioItem,
    PortfolioResearchRequest,
    AllocationMethod
)

class ResearchAllocationEngine:

    def allocate(self, candidates: list[ResearchPortfolioItem], request: PortfolioResearchRequest) -> list[ResearchPortfolioItem]:
        target_exposure = request.target_gross_exposure
        method = request.allocation_method

        if method == AllocationMethod.EQUAL_WEIGHT:
            return self.equal_weight(candidates, target_exposure)
        elif method == AllocationMethod.SCORE_WEIGHTED:
            return self.score_weighted(candidates, target_exposure)
        elif method == AllocationMethod.VOLATILITY_ADJUSTED:
            # Requires volatility_by_symbol dict; using hybrid for simple fallback if not provided
            return self.hybrid(candidates, request)
        elif method == AllocationMethod.CONSENSUS_WEIGHTED:
            return self.consensus_weighted(candidates, target_exposure)
        else: # HYBRID and default
            return self.hybrid(candidates, request)

    def equal_weight(self, candidates: list[ResearchPortfolioItem], target_gross_exposure: float) -> list[ResearchPortfolioItem]:
        valid = [c for c in candidates if c.state != "BLOCKED_BY_LIFECYCLE" and c.state != "BLOCKED_BY_RISK"]
        if not valid:
            return candidates

        w = target_gross_exposure / len(valid)
        for c in candidates:
            if c in valid:
                c.proposed_weight = w
                c.reasons.append("Equal weight allocation applied")
            else:
                c.proposed_weight = 0.0
        return candidates

    def score_weighted(self, candidates: list[ResearchPortfolioItem], target_gross_exposure: float) -> list[ResearchPortfolioItem]:
        valid = [c for c in candidates if c.state != "BLOCKED_BY_LIFECYCLE" and c.state != "BLOCKED_BY_RISK"]
        total_score = sum((c.score or 1.0) for c in valid)

        if total_score <= 0:
            return self.equal_weight(candidates, target_gross_exposure)

        for c in candidates:
            if c in valid:
                s = c.score or 1.0
                c.proposed_weight = (s / total_score) * target_gross_exposure
                c.reasons.append(f"Score weighted allocation applied (score: {s})")
            else:
                c.proposed_weight = 0.0
        return candidates

    def volatility_adjusted(self, candidates: list[ResearchPortfolioItem], volatility_by_symbol: dict[str, float], target_gross_exposure: float) -> list[ResearchPortfolioItem]:
        valid = [c for c in candidates if c.state != "BLOCKED_BY_LIFECYCLE" and c.state != "BLOCKED_BY_RISK"]
        inv_vols = []
        for c in valid:
            vol = volatility_by_symbol.get(c.symbol, 0.0)
            if vol <= 0: vol = 0.01
            inv_vols.append(1.0 / vol)

        total_inv_vol = sum(inv_vols)
        if total_inv_vol <= 0:
            return self.equal_weight(candidates, target_gross_exposure)

        for i, c in enumerate(valid):
            c.proposed_weight = (inv_vols[i] / total_inv_vol) * target_gross_exposure
            c.reasons.append("Volatility adjusted allocation applied")

        for c in candidates:
            if c not in valid:
                c.proposed_weight = 0.0
        return candidates

    def consensus_weighted(self, candidates: list[ResearchPortfolioItem], target_gross_exposure: float) -> list[ResearchPortfolioItem]:
        valid = [c for c in candidates if c.state != "BLOCKED_BY_LIFECYCLE" and c.state != "BLOCKED_BY_RISK"]
        total_score = sum((c.consensus_score or 1.0) for c in valid)

        if total_score <= 0:
            return self.equal_weight(candidates, target_gross_exposure)

        for c in candidates:
            if c in valid:
                s = c.consensus_score or 1.0
                c.proposed_weight = (s / total_score) * target_gross_exposure
                c.reasons.append(f"Consensus weighted allocation applied (consensus: {s})")
            else:
                c.proposed_weight = 0.0
        return candidates

    def hybrid(self, candidates: list[ResearchPortfolioItem], request: PortfolioResearchRequest, volatility_by_symbol: dict[str, float] | None = None) -> list[ResearchPortfolioItem]:
        valid = [c for c in candidates if c.state != "BLOCKED_BY_LIFECYCLE" and c.state != "BLOCKED_BY_RISK"]
        hybrid_scores = []

        for c in valid:
            base = c.score or 50.0
            cons = c.consensus_score or 50.0
            fund = c.fundamental_score or 50.0
            rs = c.relative_strength_score or 50.0
            risk = c.risk_score or 50.0

            # Simple hybrid logic
            hs = (base * 0.3) + (cons * 0.3) + (fund * 0.2) + (rs * 0.2)
            # Penalty for high risk
            hs = hs * (1.0 - (risk / 200.0))

            hybrid_scores.append(max(0.1, hs))

        total_hs = sum(hybrid_scores)
        if total_hs <= 0:
            return self.equal_weight(candidates, request.target_gross_exposure)

        for i, c in enumerate(valid):
            c.proposed_weight = (hybrid_scores[i] / total_hs) * request.target_gross_exposure
            c.reasons.append(f"Hybrid allocation applied (hybrid score: {hybrid_scores[i]:.2f})")

        for c in candidates:
            if c not in valid:
                c.proposed_weight = 0.0

        return candidates
