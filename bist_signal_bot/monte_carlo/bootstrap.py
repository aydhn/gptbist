from typing import Any

from bist_signal_bot.monte_carlo.models import ResamplingMethod, MonteCarloPath
from bist_signal_bot.monte_carlo.resampling import ResamplingEngine

class BootstrapEngine:
    def __init__(self, resampling_engine: ResamplingEngine | None = None):
        self.resampling_engine = resampling_engine or ResamplingEngine()

    def bootstrap_trades(self, trades: list[dict[str, Any]], simulations: int, seed: int, method: ResamplingMethod = ResamplingMethod.TRADE_BOOTSTRAP) -> list[list[dict[str, Any]]]:
        if not trades:
            return []

        results = []
        for i in range(simulations):
            path_seed = seed + i
            if method == ResamplingMethod.TRADE_SHUFFLE:
                resampled = self.resampling_engine.trade_shuffle(trades, path_seed)
            else:
                resampled = self.resampling_engine.trade_bootstrap(trades, path_seed)
            results.append(resampled)
        return results

    def bootstrap_returns(self, returns: list[float], simulations: int, seed: int, method: ResamplingMethod = ResamplingMethod.RETURN_BOOTSTRAP, block_size: int | None = None) -> list[list[float]]:
        if not returns:
            return []

        results = []
        n = len(returns)
        for i in range(simulations):
            path_seed = seed + i
            resampled = self.resampling_engine.resample(returns, method, n, path_seed, block_size)
            results.append(resampled)
        return results

    def validate_sample_size(self, values_count: int, simulations: int) -> list[str]:
        warnings = []
        if values_count < 30:
            warnings.append(f"Sample size ({values_count}) is very small. Statistical confidence will be low.")
        if simulations > 10000:
            warnings.append(f"High number of simulations ({simulations}) may cause performance issues.")
        return warnings
