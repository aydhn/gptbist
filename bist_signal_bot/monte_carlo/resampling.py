from typing import Any
import math

from bist_signal_bot.core.exceptions import ResamplingError
from bist_signal_bot.monte_carlo.models import ResamplingMethod
from bist_signal_bot.monte_carlo.randomness import MonteCarloRandomState

class ResamplingEngine:
    def __init__(self, random_state: MonteCarloRandomState | None = None):
        self.random_state = random_state or MonteCarloRandomState()

    def resample(self, values: list[float], method: ResamplingMethod, size: int, seed: int, block_size: int | None = None) -> list[float]:
        if not values:
            return []

        if method == ResamplingMethod.RETURN_BOOTSTRAP:
            return self.return_bootstrap(values, seed, size)
        elif method == ResamplingMethod.BLOCK_BOOTSTRAP:
            bs = block_size if block_size is not None else max(1, len(values) // 10)
            return self.block_bootstrap(values, bs, seed, size)
        elif method == ResamplingMethod.STATIONARY_BOOTSTRAP:
            bs = block_size if block_size is not None else max(1, len(values) // 10)
            return self.stationary_bootstrap(values, bs, seed, size)
        elif method == ResamplingMethod.PARAMETRIC_NORMAL:
            if len(values) < 2:
                raise ResamplingError("Not enough data for PARAMETRIC_NORMAL.")
            try:
                import numpy as np
                mean = float(np.mean(values))
                std = float(np.std(values))
            except ImportError:
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
                std = math.sqrt(variance)
            return self.random_state.normal(mean, std, size, seed)
        elif method == ResamplingMethod.EMPIRICAL_PATH:
            return list(values)
        else:
            raise ResamplingError(f"Unsupported resampling method for values: {method}")

    def trade_bootstrap(self, trades: list[dict[str, Any]], seed: int, size: int | None = None) -> list[dict[str, Any]]:
        n = len(trades)
        if n == 0:
            return []
        target_size = size if size is not None else n
        indices = self.random_state.sample_indices(n, target_size, seed, replace=True)
        return [dict(trades[i]) for i in indices]

    def trade_shuffle(self, trades: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
        return self.random_state.shuffle_sequence([dict(t) for t in trades], seed)

    def return_bootstrap(self, returns: list[float], seed: int, size: int | None = None) -> list[float]:
        n = len(returns)
        if n == 0:
            return []
        target_size = size if size is not None else n
        indices = self.random_state.sample_indices(n, target_size, seed, replace=True)
        return [returns[i] for i in indices]

    def block_bootstrap(self, returns: list[float], block_size: int, seed: int, size: int | None = None) -> list[float]:
        n = len(returns)
        if n == 0:
            return []
        target_size = size if size is not None else n
        if block_size > n:
            block_size = n
        if block_size <= 0:
            block_size = 1

        resampled = []
        rng = self.random_state.create_rng(seed)

        while len(resampled) < target_size:
            start_idx = rng.integers(0, n) if hasattr(rng, 'integers') else rng.randint(0, n - 1)
            for i in range(block_size):
                if len(resampled) >= target_size:
                    break
                idx = (start_idx + i) % n
                resampled.append(returns[idx])
        return resampled

    def stationary_bootstrap(self, returns: list[float], avg_block_size: int, seed: int, size: int | None = None) -> list[float]:
        n = len(returns)
        if n == 0:
            return []
        target_size = size if size is not None else n
        if avg_block_size <= 0:
            avg_block_size = 1

        p = 1.0 / avg_block_size
        resampled = []
        rng = self.random_state.create_rng(seed)

        current_idx = rng.integers(0, n) if hasattr(rng, 'integers') else rng.randint(0, n - 1)

        while len(resampled) < target_size:
            resampled.append(returns[current_idx])

            rand_val = rng.uniform(0, 1) if hasattr(rng, 'uniform') else rng.random()
            if rand_val < p:
                current_idx = rng.integers(0, n) if hasattr(rng, 'integers') else rng.randint(0, n - 1)
            else:
                current_idx = (current_idx + 1) % n

        return resampled
