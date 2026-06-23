import numpy as np

from bist_signal_bot.stress.models import (
    ReturnSeries,
    MonteCarloResult,
    RiskOfRuinResult,
    StressStatus
)

class RiskOfRuinEstimator:

    def estimate(self, series: ReturnSeries, monte_carlo_result: MonteCarloResult | None, ruin_threshold_pct: float) -> RiskOfRuinResult:
        warnings = []
        status = StressStatus.PASS

        if not series.returns:
            warnings.append("Return series is empty.")
            return RiskOfRuinResult(
                status=StressStatus.ERROR,
                ruin_threshold_pct=ruin_threshold_pct,
                warnings=warnings
            )

        worst_streak = self.worst_loss_streak(series.returns)
        exp_streak = self.expected_loss_streak(series.returns)
        buffer = self.required_buffer_estimate(series)

        ruin_prob = None
        if monte_carlo_result and monte_carlo_result.sample_paths:
            # Reconstruct initial_value implicitly assuming starting value is the first element
            # Actually, standardizing on a 100k start in MC
            init_val = monte_carlo_result.sample_paths[0][0] if monte_carlo_result.sample_paths else 100000.0
            ruin_prob = self.ruin_probability_from_paths(
                monte_carlo_result.sample_paths,
                init_val,
                ruin_threshold_pct
            )
        else:
            warnings.append("Monte Carlo paths not provided. Ruin probability estimate relies on basic stats.")

        if ruin_prob is not None and ruin_prob > 10.0:
            status = StressStatus.WARN
        if ruin_prob is not None and ruin_prob > 25.0:
            status = StressStatus.FAIL

        return RiskOfRuinResult(
            status=status,
            ruin_threshold_pct=ruin_threshold_pct,
            estimated_ruin_probability_pct=ruin_prob,
            expected_loss_streak=exp_streak,
            worst_loss_streak=worst_streak,
            required_buffer_estimate_pct=buffer,
            warnings=warnings
        )

    def loss_streaks(self, returns: list[float]) -> list[int]:
        streaks = []
        current = 0
        for r in returns:
            if r < 0:
                current += 1
            elif current > 0:
                streaks.append(current)
                current = 0
        if current > 0:
            streaks.append(current)
        return streaks

    def worst_loss_streak(self, returns: list[float]) -> int | None:
        streaks = self.loss_streaks(returns)
        return max(streaks) if streaks else 0

    def expected_loss_streak(self, returns: list[float]) -> int | None:
        streaks = self.loss_streaks(returns)
        return int(round(sum(streaks) / len(streaks))) if streaks else 0

    def ruin_probability_from_paths(self, paths: list[list[float]], initial_value: float, ruin_threshold_pct: float) -> float | None:
        if not paths:
            return None

        ruined_count = 0
        ruin_value = initial_value * (1.0 - (ruin_threshold_pct / 100.0))

        for path in paths:
            arr = np.array(path)
            # Find if the path ever drops below the ruin threshold
            if np.any(arr <= ruin_value):
                ruined_count += 1

        return (ruined_count / len(paths)) * 100.0

    def required_buffer_estimate(self, series: ReturnSeries, confidence_pct: float = 95.0) -> float | None:
        if not series.returns:
            return None

        arr = np.array(series.returns)
        mean_ret = np.mean(arr)
        std_ret = np.std(arr)

        # Simple parametric Value at Risk for a 1 month horizon approx
        horizon = 21
        z_score = 1.645 # 95%
        if confidence_pct == 99.0:
            z_score = 2.326

        var = (mean_ret * horizon) - (z_score * std_ret * np.sqrt(horizon))
        # Return as a positive percentage buffer required
        return abs(var) * 100.0 if var < 0 else 0.0
