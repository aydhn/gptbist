import pytest
from bist_signal_bot.benchmarks.registry import BenchmarkRegistry, create_default_benchmark_registry
from bist_signal_bot.benchmarks.strategies import CashBenchmark
from bist_signal_bot.core.exceptions import BenchmarkRegistryError

def test_registry_default():
    reg = create_default_benchmark_registry()
    names = reg.list_names()
    assert "buy_and_hold" in names
    assert "cash" in names

def test_registry_duplicate():
    reg = BenchmarkRegistry()
    reg.register(CashBenchmark())
    with pytest.raises(BenchmarkRegistryError):
        reg.register(CashBenchmark())

def test_registry_missing():
    reg = BenchmarkRegistry()
    with pytest.raises(BenchmarkRegistryError):
        reg.get("unknown_benchmark")
