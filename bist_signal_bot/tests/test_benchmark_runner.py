import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.performance.benchmark import BenchmarkRunner
from bist_signal_bot.performance.profiler import LocalProfiler
from bist_signal_bot.performance.models import BenchmarkRequest, BenchmarkType
from bist_signal_bot.core.exceptions import BenchmarkError

def test_benchmark_synthetic_scanner():
    runner = BenchmarkRunner(profiler=LocalProfiler())
    req = BenchmarkRequest(benchmark_type=BenchmarkType.SCANNER, iterations=1, warmup_iterations=0)
    res = runner.run(req)
    assert len(res.profiles) == 1

def test_benchmark_heavy_rejects_without_confirm():
    settings = Settings(PERFORMANCE_HEAVY_BENCHMARK_REQUIRES_CONFIRM=True)
    runner = BenchmarkRunner(profiler=LocalProfiler(), settings=settings)
    req = BenchmarkRequest(benchmark_type=BenchmarkType.SCANNER, heavy=True)
    with pytest.raises(BenchmarkError):
        runner.run(req, confirm_heavy=False)
