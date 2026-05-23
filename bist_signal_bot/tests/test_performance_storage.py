import pytest
from bist_signal_bot.performance.storage import PerformanceStore
from bist_signal_bot.performance.models import BenchmarkRunResult, BenchmarkRequest, BenchmarkType, PerformanceStatus

def test_storage_save_load_benchmark(tmp_path):
    store = PerformanceStore(base_dir=tmp_path)
    req = BenchmarkRequest(benchmark_type=BenchmarkType.SCANNER)
    bench = BenchmarkRunResult(benchmark_id="b1", request=req, status=PerformanceStatus.PASS)
    store.save_benchmark(bench)

    loaded = store.load_benchmark("b1")
    assert loaded is not None
    assert loaded.benchmark_id == "b1"
