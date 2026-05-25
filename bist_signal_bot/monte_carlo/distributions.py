import uuid
import math
from typing import Any

from bist_signal_bot.monte_carlo.models import MonteCarloMetricType, MonteCarloDistribution, MonteCarloMetric, MonteCarloStatus

class DistributionAnalyzer:
    def build_distribution(self, metric_type: MonteCarloMetricType, values: list[float], observed_value: float | None = None) -> MonteCarloDistribution:
        warnings = []
        if not values:
            warnings.append("Empty values provided for distribution.")
            return MonteCarloDistribution(
                distribution_id=str(uuid.uuid4()),
                metric_type=metric_type,
                values=[],
                percentiles={},
                observations_count=0,
                observed_value=observed_value,
                warnings=warnings
            )

        sorted_vals = sorted(values)
        percentiles = {
            "p05": self.percentile(sorted_vals, 0.05) or 0.0,
            "p25": self.percentile(sorted_vals, 0.25) or 0.0,
            "p50": self.percentile(sorted_vals, 0.50) or 0.0,
            "p75": self.percentile(sorted_vals, 0.75) or 0.0,
            "p95": self.percentile(sorted_vals, 0.95) or 0.0
        }

        return MonteCarloDistribution(
            distribution_id=str(uuid.uuid4()),
            metric_type=metric_type,
            values=sorted_vals,
            percentiles=percentiles,
            observations_count=len(sorted_vals),
            observed_value=observed_value,
            warnings=warnings
        )

    def summary_metric(self, distribution: MonteCarloDistribution) -> MonteCarloMetric:
        vals = distribution.values
        if not vals:
            return MonteCarloMetric(
                metric_id=str(uuid.uuid4()),
                metric_type=distribution.metric_type,
                name=distribution.metric_type.value,
                status=MonteCarloStatus.INSUFFICIENT_DATA,
                warnings=distribution.warnings
            )

        mean = sum(vals) / len(vals)
        if len(vals) > 1:
            variance = sum((x - mean) ** 2 for x in vals) / (len(vals) - 1)
            std = math.sqrt(variance)
        else:
            std = 0.0

        return MonteCarloMetric(
            metric_id=str(uuid.uuid4()),
            metric_type=distribution.metric_type,
            name=distribution.metric_type.value,
            status=MonteCarloStatus.PASS,
            mean=mean,
            median=distribution.percentiles.get("p50"),
            std=std,
            p05=distribution.percentiles.get("p05"),
            p25=distribution.percentiles.get("p25"),
            p75=distribution.percentiles.get("p75"),
            p95=distribution.percentiles.get("p95"),
            min_value=vals[0],
            max_value=vals[-1],
            observed_value=distribution.observed_value,
            warnings=distribution.warnings
        )

    def percentile(self, values: list[float], p: float) -> float | None:
        if not values:
            return None
        sorted_vals = sorted(values)
        k = (len(sorted_vals) - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        d0 = sorted_vals[int(f)] * (c - k)
        d1 = sorted_vals[int(c)] * (k - f)
        return d0 + d1

    def percentile_rank(self, values: list[float], observed_value: float) -> float | None:
        if not values:
            return None
        count_below = sum(1 for v in values if v < observed_value)
        count_equal = sum(1 for v in values if v == observed_value)
        return (count_below + 0.5 * count_equal) / len(values) * 100.0

    def tail_metrics(self, values: list[float]) -> dict[str, float | None]:
        if not values:
            return {"cvar_5": None, "p05": None, "p01": None}

        p05 = self.percentile(values, 0.05)
        p01 = self.percentile(values, 0.01)

        tail_vals = [v for v in values if p05 is not None and v <= p05]
        cvar = sum(tail_vals) / len(tail_vals) if tail_vals else p05

        return {
            "cvar_5": cvar,
            "p05": p05,
            "p01": p01
        }
