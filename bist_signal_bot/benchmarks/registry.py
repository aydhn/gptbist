from typing import Optional

from bist_signal_bot.benchmarks.base import BaseBenchmarkStrategy
from bist_signal_bot.benchmarks.models import BenchmarkCategory, BenchmarkSpec
from bist_signal_bot.core.exceptions import BenchmarkRegistryError


class BenchmarkRegistry:
    """Registry for benchmark strategies."""

    def __init__(self):
        self._benchmarks: dict[str, BaseBenchmarkStrategy] = {}

    def register(self, benchmark: BaseBenchmarkStrategy) -> None:
        """Register a new benchmark."""
        name = benchmark.spec.name.lower().strip()
        if name in self._benchmarks:
            raise BenchmarkRegistryError(f"Benchmark '{name}' is already registered.")
        self._benchmarks[name] = benchmark

    def get(self, name: str) -> BaseBenchmarkStrategy:
        """Retrieve a benchmark by name."""
        name_norm = name.lower().strip()
        if name_norm not in self._benchmarks:
            raise BenchmarkRegistryError(f"Benchmark '{name_norm}' not found in registry.")
        return self._benchmarks[name_norm]

    def exists(self, name: str) -> bool:
        """Check if a benchmark exists in the registry."""
        return name.lower().strip() in self._benchmarks

    def list_specs(self, category: Optional[BenchmarkCategory] = None) -> list[BenchmarkSpec]:
        """List specs of registered benchmarks, optionally filtered by category."""
        specs = [b.spec for b in self._benchmarks.values()]
        if category:
            specs = [s for s in specs if s.category == category]
        return specs

    def list_names(self, category: Optional[BenchmarkCategory] = None) -> list[str]:
        """List names of registered benchmarks, optionally filtered by category."""
        specs = self.list_specs(category)
        return [s.name for s in specs]


def create_default_benchmark_registry() -> BenchmarkRegistry:
    """Create and populate a BenchmarkRegistry with built-in benchmarks."""
    from bist_signal_bot.benchmarks.strategies import (
        BuyAndHoldBenchmark,
        CashBenchmark,
        EqualWeightBenchmark,
        MovingAverageBenchmark,
        NaiveMomentumBenchmark,
        NaiveVolatilityFilterBenchmark,
        DeterministicRandomBaselineBenchmark
    )

    registry = BenchmarkRegistry()
    registry.register(BuyAndHoldBenchmark())
    registry.register(CashBenchmark())
    registry.register(EqualWeightBenchmark())
    registry.register(MovingAverageBenchmark())
    registry.register(NaiveMomentumBenchmark())
    registry.register(NaiveVolatilityFilterBenchmark())
    registry.register(DeterministicRandomBaselineBenchmark())

    return registry
