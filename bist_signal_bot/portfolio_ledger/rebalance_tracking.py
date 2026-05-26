from datetime import datetime, timezone
import uuid
from typing import Any

from bist_signal_bot.portfolio_ledger.models import (
    ResearchPortfolio,
    RebalanceTrackingResult,
    PortfolioValuationSnapshot
)

class RebalanceTracker:
    def __init__(self):
        pass

    def track_rebalance(
        self,
        portfolio: ResearchPortfolio,
        rebalance_simulation: Any,
        before_snapshot: PortfolioValuationSnapshot | None = None,
        after_snapshot: PortfolioValuationSnapshot | None = None
    ) -> RebalanceTrackingResult:

        before_nav = before_snapshot.simulated_nav if before_snapshot else portfolio.current_simulated_nav
        after_nav = after_snapshot.simulated_nav if after_snapshot else portfolio.current_simulated_nav

        before_score = getattr(rebalance_simulation, "score_before", None)
        after_score = getattr(rebalance_simulation, "score_after", None)

        q_delta = self.quality_delta(before_score, after_score)

        result = RebalanceTrackingResult(
            tracking_id=f"rebtrk_{uuid.uuid4().hex[:8]}",
            portfolio_id=portfolio.portfolio_id,
            rebalance_id=getattr(rebalance_simulation, "rebalance_id", None),
            generated_at=datetime.now(timezone.utc),
            before_nav=before_nav,
            after_nav=after_nav,
            estimated_turnover_pct=getattr(rebalance_simulation, "estimated_turnover_pct", None),
            realized_simulated_turnover_pct=getattr(rebalance_simulation, "realized_turnover_pct", None),
            estimated_cost_bps=getattr(rebalance_simulation, "estimated_cost_bps", None),
            simulated_cost_bps=getattr(rebalance_simulation, "simulated_cost_bps", None),
            before_score=before_score,
            after_score=after_score,
            quality_delta=q_delta,
            violations_before=getattr(rebalance_simulation, "violations_before", 0),
            violations_after=getattr(rebalance_simulation, "violations_after", 0)
        )
        return result

    def quality_delta(self, before_score: float | None, after_score: float | None) -> float | None:
        if before_score is None or after_score is None:
            return None
        return after_score - before_score

    def compare_violations(self, before_count: int, after_count: int) -> dict[str, Any]:
        resolved = max(0, before_count - after_count)
        new_violations = max(0, after_count - before_count)
        return {
            "resolved": resolved,
            "new": new_violations,
            "net_change": after_count - before_count
        }

    def summarize_rebalance_effect(self, result: RebalanceTrackingResult) -> list[str]:
        summary = []
        if result.quality_delta is not None:
            direction = "improved" if result.quality_delta > 0 else "degraded"
            summary.append(f"Portfolio quality score {direction} by {abs(result.quality_delta):.2f} points.")

        if result.estimated_turnover_pct is not None:
            summary.append(f"Estimated turnover: {result.estimated_turnover_pct:.2f}%")

        if result.violations_after < result.violations_before:
            summary.append(f"Constraint violations reduced from {result.violations_before} to {result.violations_after}.")

        return summary
