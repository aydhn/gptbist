import random
from typing import Any

class MonteCarloRandomState:
    def __init__(self):
        try:
            import numpy as np
            self._np = np
        except ImportError:
            self._np = None

    def create_rng(self, seed: int) -> Any:
        if self._np:
            return self._np.random.default_rng(seed)
        return random.Random(seed)

    def sample_indices(self, n: int, size: int, seed: int, replace: bool = True) -> list[int]:
        if size <= 0 or n <= 0:
            return []
        rng = self.create_rng(seed)
        if self._np:
            return rng.choice(n, size=size, replace=replace).tolist()

        if replace:
            return [rng.randint(0, n - 1) for _ in range(size)]
        else:
            if size > n:
                raise ValueError("Cannot sample without replacement if size > n")
            return rng.sample(range(n), size)

    def shuffle_sequence(self, values: list[Any], seed: int) -> list[Any]:
        if not values:
            return []
        result = list(values)
        rng = self.create_rng(seed)
        if self._np:
            rng.shuffle(result)
        else:
            rng.shuffle(result)
        return result

    def uniform(self, low: float, high: float, size: int, seed: int) -> list[float]:
        if size <= 0:
            return []
        rng = self.create_rng(seed)
        if self._np:
            return rng.uniform(low, high, size=size).tolist()
        return [rng.uniform(low, high) for _ in range(size)]

    def normal(self, mean: float, std: float, size: int, seed: int) -> list[float]:
        if size <= 0:
            return []
        rng = self.create_rng(seed)
        if self._np:
            return rng.normal(mean, std, size=size).tolist()
        return [rng.gauss(mean, std) for _ in range(size)]
