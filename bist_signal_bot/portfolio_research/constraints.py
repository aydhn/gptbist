import uuid
from typing import Any
from bist_signal_bot.portfolio_research.models import (
    ResearchPortfolioItem,
    PortfolioResearchRequest,
    PortfolioConstraint,
    PortfolioConstraintStatus
)

class PortfolioConstraintEngine:
    """Applies research portfolio constraints to signal candidates."""

    def validate_items(self, items: list[ResearchPortfolioItem], request: PortfolioResearchRequest) -> list[PortfolioConstraint]:
        constraints = []

        # We perform checks on the requested limits, e.g. min_score
        for item in items:
            if item.score is not None and item.score < request.min_score:
                item.warnings.append(f"Score {item.score} < min_score {request.min_score}")
                item.state = "BLOCKED_BY_SCORE"

            if item.state == "INVALIDATED" or item.state == "EXPIRED" or item.state == "ARCHIVED":
                item.warnings.append(f"Lifecycle state {item.state} invalidates allocation")
                item.state = "BLOCKED_BY_LIFECYCLE"

            if item.risk_score is not None and item.risk_score > 90:
                item.warnings.append("Risk score too high")
                item.state = "BLOCKED_BY_RISK"

        # Max symbol weight
        symbol_constraint = PortfolioConstraint(
            constraint_id=str(uuid.uuid4()),
            name="Max Symbol Weight",
            status=PortfolioConstraintStatus.PASS,
            message=f"Checked max symbol weight {request.max_symbol_weight}",
            limit_value=request.max_symbol_weight
        )
        for item in items:
            if item.proposed_weight > request.max_symbol_weight:
                symbol_constraint.status = PortfolioConstraintStatus.WARN
                symbol_constraint.affected_symbols.append(item.symbol)
        constraints.append(symbol_constraint)

        # Max sector weight
        sector_weights = {}
        for item in items:
            if item.sector and item.proposed_weight > 0:
                sector_weights[item.sector] = sector_weights.get(item.sector, 0.0) + item.proposed_weight

        sector_constraint = PortfolioConstraint(
            constraint_id=str(uuid.uuid4()),
            name="Max Sector Weight",
            status=PortfolioConstraintStatus.PASS,
            message=f"Checked max sector weight {request.max_sector_weight}",
            limit_value=request.max_sector_weight
        )
        for sec, w in sector_weights.items():
            if w > request.max_sector_weight:
                sector_constraint.status = PortfolioConstraintStatus.WARN
                sector_constraint.message = f"Sector {sec} weight {w:.2f} > limit {request.max_sector_weight}"
        constraints.append(sector_constraint)

        return constraints

    def apply_weight_caps(self, items: list[ResearchPortfolioItem], request: PortfolioResearchRequest) -> list[ResearchPortfolioItem]:
        sector_weights = {}
        strategy_weights = {}

        for item in items:
            if item.state and "BLOCKED" in item.state:
                item.capped_weight = 0.0
                continue

            w = min(item.proposed_weight, request.max_symbol_weight)
            item.capped_weight = w

        for item in items:
            sec = item.sector or "UNKNOWN"
            strat = item.strategy_name or "UNKNOWN"
            sector_weights[sec] = sector_weights.get(sec, 0.0) + item.capped_weight
            strategy_weights[strat] = strategy_weights.get(strat, 0.0) + item.capped_weight

        # Very simple proportional capping for sectors/strategies if needed
        # Real logic might be iterative. We do a one-pass scale down here for simplicity.
        for item in items:
            sec = item.sector or "UNKNOWN"
            strat = item.strategy_name or "UNKNOWN"

            sec_ratio = 1.0
            if sector_weights[sec] > request.max_sector_weight:
                sec_ratio = request.max_sector_weight / sector_weights[sec]

            strat_ratio = 1.0
            if strategy_weights[strat] > request.max_strategy_weight:
                strat_ratio = request.max_strategy_weight / strategy_weights[strat]

            scale = min(sec_ratio, strat_ratio)
            item.capped_weight *= scale

        return items

    def normalize_final_weights(self, items: list[ResearchPortfolioItem], target_gross_exposure: float) -> list[ResearchPortfolioItem]:
        total_w = sum(item.capped_weight for item in items)
        if total_w <= 0:
            for item in items:
                item.final_weight = 0.0
            return items

        if total_w > target_gross_exposure:
            scale = target_gross_exposure / total_w
            for item in items:
                item.final_weight = item.capped_weight * scale
        else:
            for item in items:
                item.final_weight = item.capped_weight

        # Zero out extremely small weights
        for item in items:
            if item.final_weight < 0.001:
                item.final_weight = 0.0

        return items

    def constraint_summary(self, constraints: list[PortfolioConstraint]) -> dict[str, Any]:
        return {
            "total_constraints": len(constraints),
            "pass_count": sum(1 for c in constraints if c.status == PortfolioConstraintStatus.PASS),
            "warn_count": sum(1 for c in constraints if c.status == PortfolioConstraintStatus.WARN),
            "fail_count": sum(1 for c in constraints if c.status == PortfolioConstraintStatus.FAIL),
        }
