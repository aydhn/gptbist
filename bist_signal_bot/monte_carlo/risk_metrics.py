import uuid
import math
from typing import Any

from bist_signal_bot.monte_carlo.models import MonteCarloPath, MonteCarloRiskSummary

class MonteCarloRiskAnalyzer:
    def risk_summary(self, paths: list[MonteCarloPath], initial_equity: float, ruin_threshold_pct: float, drawdown_threshold_pct: float | None = None) -> MonteCarloRiskSummary:
        if not paths:
            return MonteCarloRiskSummary(summary_id=str(uuid.uuid4()))

        final_equities = [p.final_equity for p in paths]
        final_equities.sort()

        n = len(paths)
        ruin_prob = self.ruin_probability(paths)
        neg_ret_prob = self.probability_negative_return(paths, initial_equity)

        dd_prob = None
        if drawdown_threshold_pct is not None:
            dd_prob = self.probability_drawdown_above(paths, drawdown_threshold_pct)

        cvar5 = self.cvar(final_equities, 0.05)
        etl5 = self.expected_tail_loss(final_equities, 0.05)

        median_eq = self._percentile(final_equities, 0.50)
        p05_eq = self._percentile(final_equities, 0.05)
        p95_eq = self._percentile(final_equities, 0.95)

        warnings = []
        if ruin_prob is not None and ruin_prob > 25.0:
            warnings.append(f"High probability of ruin: {ruin_prob:.2f}%")
        if neg_ret_prob is not None and neg_ret_prob > 45.0:
            warnings.append(f"High probability of negative return: {neg_ret_prob:.2f}%")

        return MonteCarloRiskSummary(
            summary_id=str(uuid.uuid4()),
            ruin_probability_pct=ruin_prob,
            probability_negative_return_pct=neg_ret_prob,
            probability_drawdown_above_threshold_pct=dd_prob,
            expected_tail_loss_pct=etl5,
            cvar_5_pct=cvar5,
            median_final_equity=median_eq,
            p05_final_equity=p05_eq,
            p95_final_equity=p95_eq,
            warnings=warnings
        )

    def ruin_probability(self, paths: list[MonteCarloPath]) -> float | None:
        if not paths:
            return None
        hits = sum(1 for p in paths if p.ruin_hit)
        return (hits / len(paths)) * 100.0

    def probability_negative_return(self, paths: list[MonteCarloPath], initial_equity: float = 100000.0) -> float | None:
        if not paths:
            return None
        hits = sum(1 for p in paths if p.final_equity < initial_equity)
        return (hits / len(paths)) * 100.0

    def probability_drawdown_above(self, paths: list[MonteCarloPath], threshold_pct: float) -> float | None:
        if not paths:
            return None
        hits = sum(1 for p in paths if p.max_drawdown_pct > threshold_pct)
        return (hits / len(paths)) * 100.0

    def cvar(self, values: list[float], alpha: float = 0.05) -> float | None:
        if not values:
            return None
        sorted_vals = sorted(values)
        k = max(1, int(len(sorted_vals) * alpha))
        tail = sorted_vals[:k]
        return sum(tail) / len(tail) if tail else sorted_vals[0]

    def expected_tail_loss(self, values: list[float], alpha: float = 0.05) -> float | None:
        return self.cvar(values, alpha)

    def _percentile(self, sorted_vals: list[float], p: float) -> float | None:
        if not sorted_vals:
            return None
        k = (len(sorted_vals) - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        return sorted_vals[int(f)] * (c - k) + sorted_vals[int(c)] * (k - f)
