import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.performance.baseline import PerformanceBaselineManager
from bist_signal_bot.performance.models import BenchmarkRequest, BenchmarkRunResult, BenchmarkType, PerformanceStatus
from bist_signal_bot.core.exceptions import PerformanceBaselineError

def test_baseline_create_requires_confirm(tmp_path):
    mgr = PerformanceBaselineManager(base_dir=tmp_path)
    req = BenchmarkRequest(benchmark_type=BenchmarkType.SCANNER)
    res = BenchmarkRunResult(benchmark_id="1", request=req, status=PerformanceStatus.PASS)
    with pytest.raises(PerformanceBaselineError):
        mgr.create_baseline(res, confirm=False)

def test_baseline_save_load(tmp_path):
    mgr = PerformanceBaselineManager(base_dir=tmp_path)
    req = BenchmarkRequest(benchmark_type=BenchmarkType.SCANNER)
    res = BenchmarkRunResult(benchmark_id="1", request=req, status=PerformanceStatus.PASS, median_elapsed_seconds=1.0)
    base = mgr.create_baseline(res, confirm=True)
    mgr.save_baseline(base)

    loaded = mgr.load_latest_baseline(BenchmarkType.SCANNER)
    assert loaded is not None
    assert loaded.baseline_id == base.baseline_id
