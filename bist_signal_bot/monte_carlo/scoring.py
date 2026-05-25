from typing import Any

from bist_signal_bot.monte_carlo.models import (
    MonteCarloResult,
    MonteCarloRiskSummary,
    MonteCarloMetric,
    RealityCheckResult,
    RealityCheckStatus,
    MonteCarloStatus
)

class MonteCarloRobustnessScorer:
    def score(self, risk_summary: MonteCarloRiskSummary | None, reality_check: RealityCheckResult | None, metrics: list[MonteCarloMetric]) -> float | None:
        if not risk_summary and not reality_check and not metrics:
            return None

        base_score = 100.0

        if risk_summary:
            if risk_summary.ruin_probability_pct is not None:
                if risk_summary.ruin_probability_pct > 25.0:
                    base_score -= 40.0
                elif risk_summary.ruin_probability_pct > 10.0:
                    base_score -= 20.0
                elif risk_summary.ruin_probability_pct > 0.0:
                    base_score -= (risk_summary.ruin_probability_pct * 1.5)

            if risk_summary.probability_negative_return_pct is not None:
                if risk_summary.probability_negative_return_pct > 45.0:
                    base_score -= 30.0
                elif risk_summary.probability_negative_return_pct > 25.0:
                    base_score -= 15.0

        if reality_check:
            if reality_check.status == RealityCheckStatus.LIKELY_OVERFIT:
                base_score -= 50.0
            elif reality_check.status == RealityCheckStatus.WATCH:
                base_score -= 20.0
            elif reality_check.multiple_testing_warning:
                base_score -= 10.0

        for m in metrics:
            if m.name == "MAX_DRAWDOWN" and m.p95 is not None and m.p95 > 50.0:
                base_score -= 20.0

        return max(0.0, min(100.0, base_score))

    def derive_status(self, score: float | None, warnings: list[str]) -> MonteCarloStatus:
        if score is None:
            return MonteCarloStatus.INSUFFICIENT_DATA

        if score >= 80.0:
            return MonteCarloStatus.PASS
        elif score >= 50.0:
            return MonteCarloStatus.WATCH
        else:
            return MonteCarloStatus.FAIL
