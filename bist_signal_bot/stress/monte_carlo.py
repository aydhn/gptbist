import uuid
import numpy as np
from typing import Any

from bist_signal_bot.stress.models import (
    ReturnSeries,
    MonteCarloConfig,
    MonteCarloResult,
    MonteCarloMethod,
    StressStatus
)

class MonteCarloSimulator:

    def run(self, series: ReturnSeries, config: MonteCarloConfig) -> MonteCarloResult:
        warnings = []
        status = StressStatus.PASS

        if not series.returns:
            warnings.append("Return series is empty. Cannot run Monte Carlo.")
            return MonteCarloResult(
                result_id=str(uuid.uuid4()),
                config=config,
                status=StressStatus.ERROR,
                warnings=warnings
            )

        if len(series.returns) < 30:
            warnings.append("Return series has less than 30 points. Monte Carlo results may be highly unreliable.")
            status = StressStatus.WARN

        # Generate paths based on method
        if config.method == MonteCarloMethod.BOOTSTRAP:
            paths = self.bootstrap_paths(series.returns, config)
        elif config.method == MonteCarloMethod.BLOCK_BOOTSTRAP:
            paths = self.block_bootstrap_paths(series.returns, config)
        elif config.method == MonteCarloMethod.NORMAL_PARAMETRIC:
            paths = self.normal_parametric_paths(series.returns, config)
        elif config.method == MonteCarloMethod.HISTORICAL_SHUFFLE:
            paths = self.historical_shuffle_paths(series.returns, config)
        else:
            warnings.append(f"Unknown Monte Carlo method: {config.method}. Falling back to BOOTSTRAP.")
            paths = self.bootstrap_paths(series.returns, config)
            status = StressStatus.WARN

        equity_paths = self.paths_to_equity(paths, config.initial_value)
        percentiles = self.calculate_percentiles(equity_paths, config.initial_value)

        sample_paths = equity_paths[:20]  # Limit to 20 for output size
        final_values = [p[-1] for p in equity_paths]

        return MonteCarloResult(
            result_id=str(uuid.uuid4()),
            config=config,
            status=status,
            final_values=final_values,
            final_return_pct_p05=percentiles.get("final_return_p05"),
            final_return_pct_p50=percentiles.get("final_return_p50"),
            final_return_pct_p95=percentiles.get("final_return_p95"),
            max_drawdown_pct_p05=percentiles.get("max_drawdown_p05"),
            max_drawdown_pct_p50=percentiles.get("max_drawdown_p50"),
            max_drawdown_pct_p95=percentiles.get("max_drawdown_p95"),
            sample_paths=sample_paths,
            warnings=warnings
        )

    def bootstrap_paths(self, returns: list[float], config: MonteCarloConfig) -> list[list[float]]:
        rng = np.random.default_rng(config.seed)
        paths = []
        arr = np.array(returns)
        for _ in range(config.simulations):
            path = rng.choice(arr, size=config.horizon_days, replace=True).tolist()
            paths.append(path)
        return paths

    def block_bootstrap_paths(self, returns: list[float], config: MonteCarloConfig) -> list[list[float]]:
        rng = np.random.default_rng(config.seed)
        block_size = config.block_size or 5
        paths = []
        arr = np.array(returns)
        n = len(arr)

        if n < block_size:
            return self.bootstrap_paths(returns, config)

        for _ in range(config.simulations):
            path = []
            while len(path) < config.horizon_days:
                start_idx = rng.integers(0, n - block_size + 1)
                block = arr[start_idx:start_idx + block_size].tolist()
                path.extend(block)
            paths.append(path[:config.horizon_days])
        return paths

    def normal_parametric_paths(self, returns: list[float], config: MonteCarloConfig) -> list[list[float]]:
        rng = np.random.default_rng(config.seed)
        paths = []
        mu = np.mean(returns)
        sigma = np.std(returns)
        for _ in range(config.simulations):
            path = rng.normal(mu, sigma, config.horizon_days).tolist()
            paths.append(path)
        return paths

    def historical_shuffle_paths(self, returns: list[float], config: MonteCarloConfig) -> list[list[float]]:
        rng = np.random.default_rng(config.seed)
        paths = []
        arr = np.array(returns)
        for _ in range(config.simulations):
            # Same historical returns, just shuffled order
            path_returns = arr.copy()
            rng.shuffle(path_returns)

            # If horizon > len(returns), cycle through
            if config.horizon_days > len(path_returns):
                repeated = np.tile(path_returns, int(np.ceil(config.horizon_days / len(path_returns))))
                path = repeated[:config.horizon_days].tolist()
            else:
                path = path_returns[:config.horizon_days].tolist()
            paths.append(path)
        return paths

    def paths_to_equity(self, paths: list[list[float]], initial_value: float) -> list[list[float]]:
        equity_paths = []
        for path in paths:
            # Add 1.0 to returns and calculate cumulative product, starting with initial value
            arr = np.array(path)
            cum_returns = np.cumprod(1.0 + arr)
            equity = initial_value * cum_returns
            # Prepend initial value
            equity = np.insert(equity, 0, initial_value)
            equity_paths.append(equity.tolist())
        return equity_paths

    def calculate_percentiles(self, equity_paths: list[list[float]], initial_value: float) -> dict[str, float]:
        if not equity_paths:
            return {}

        final_returns = []
        max_drawdowns = []

        for path in equity_paths:
            final_val = path[-1]
            ret_pct = ((final_val / initial_value) - 1.0) * 100.0
            final_returns.append(ret_pct)

            arr = np.array(path)
            running_max = np.maximum.accumulate(arr)
            drawdowns = (running_max - arr) / running_max * 100.0
            max_drawdowns.append(np.max(drawdowns))

        return {
            "final_return_p05": float(np.percentile(final_returns, 5)),
            "final_return_p50": float(np.percentile(final_returns, 50)),
            "final_return_p95": float(np.percentile(final_returns, 95)),
            "max_drawdown_p05": float(np.percentile(max_drawdowns, 5)), # 5th percentile of max drawdowns (best case scenario for max drawdown)
            "max_drawdown_p50": float(np.percentile(max_drawdowns, 50)),
            "max_drawdown_p95": float(np.percentile(max_drawdowns, 95))  # 95th percentile (worst case)
        }
