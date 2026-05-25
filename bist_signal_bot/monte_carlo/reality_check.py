import uuid
from typing import Any

from bist_signal_bot.monte_carlo.models import RealityCheckResult, RealityCheckStatus
from bist_signal_bot.config.settings import Settings

class RealityCheckEngine:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def run(self, observed_value: float | None, simulated_values: list[float], strategy_name: str | None = None, symbol: str | None = None, trials_count: int = 1) -> RealityCheckResult:
        warnings = []
        if observed_value is None or not simulated_values:
            return RealityCheckResult(
                reality_check_id=str(uuid.uuid4()),
                status=RealityCheckStatus.INSUFFICIENT_DATA,
                observed_metric="net_return_pct",
                trials_count=trials_count,
                strategy_name=strategy_name,
                symbol=symbol,
                warnings=["Missing observed or simulated values for reality check."]
            )

        p_val = self.simulated_p_value(observed_value, simulated_values, greater_is_better=True)

        count_below = sum(1 for v in simulated_values if v < observed_value)
        count_equal = sum(1 for v in simulated_values if v == observed_value)
        percentile_rank = (count_below + 0.5 * count_equal) / len(simulated_values) * 100.0

        status = self.classify(p_val, percentile_rank, trials_count)
        mt_warn = self.multiple_testing_warning(trials_count)

        if mt_warn:
            warnings.append(f"Multiple testing warning: {trials_count} trials were conducted. The p-value might be understated.")
        if status == RealityCheckStatus.LIKELY_OVERFIT:
            warnings.append("Reality check indicates likely overfit. The observed performance is not significantly better than random paths.")

        return RealityCheckResult(
            reality_check_id=str(uuid.uuid4()),
            status=status,
            observed_metric="net_return_pct",
            trials_count=trials_count,
            strategy_name=strategy_name,
            symbol=symbol,
            observed_value=observed_value,
            simulated_p_value=p_val,
            percentile_rank=percentile_rank,
            multiple_testing_warning=mt_warn,
            warnings=warnings
        )

    def simulated_p_value(self, observed_value: float, simulated_values: list[float], greater_is_better: bool = True) -> float | None:
        if not simulated_values:
            return None
        n = len(simulated_values)
        if greater_is_better:
            extreme_count = sum(1 for v in simulated_values if v >= observed_value)
        else:
            extreme_count = sum(1 for v in simulated_values if v <= observed_value)
        return extreme_count / n

    def multiple_testing_warning(self, trials_count: int) -> bool:
        return trials_count > self.settings.MONTE_CARLO_MULTIPLE_TESTING_TRIALS_WARN

    def classify(self, p_value: float | None, percentile_rank: float | None, trials_count: int) -> RealityCheckStatus:
        if p_value is None:
            return RealityCheckStatus.INSUFFICIENT_DATA

        adjusted_warn = self.settings.MONTE_CARLO_REALITY_PVALUE_WARN
        adjusted_fail = self.settings.MONTE_CARLO_REALITY_PVALUE_FAIL

        if p_value >= adjusted_fail:
            return RealityCheckStatus.LIKELY_OVERFIT
        elif p_value >= adjusted_warn:
            return RealityCheckStatus.WATCH
        else:
            return RealityCheckStatus.ROBUST
