import pytest
from datetime import datetime, timezone
from bist_signal_bot.performance.models import (
    ResourceSnapshot, WorkloadProfileRequest, WorkloadProfileResult, CacheReport,
    WorkloadType, PerformanceStatus, TimerResult, ConcurrencyMode
)

def test_resource_snapshot_summary():
    snap = ResourceSnapshot(timestamp=datetime.now(timezone.utc), cpu_percent=50.0, memory_percent=60.0)
    summary = snap.summary()
    assert summary["cpu_percent"] == 50.0
    assert summary["memory_percent"] == 60.0
    assert not summary["gpu_detected"]

def test_workload_profile_request_validation():
    req = WorkloadProfileRequest(workload_type=WorkloadType.SCANNER)
    assert req.iterations == 1
    assert req.max_workers == 1
    assert req.concurrency_mode == ConcurrencyMode.SERIAL

    with pytest.raises(ValueError):
        WorkloadProfileRequest(workload_type=WorkloadType.SCANNER, iterations=-1)

def test_workload_profile_result_summary():
    req = WorkloadProfileRequest(workload_type=WorkloadType.SCANNER)
    res = WorkloadProfileResult(request=req, status=PerformanceStatus.PASS, elapsed_seconds=1.5)
    summary = res.summary()
    assert summary["workload_type"] == "SCANNER"
    assert summary["status"] == "PASS"
    assert summary["elapsed_seconds"] == 1.5

def test_cache_report_summary():
    rep = CacheReport(total_size_mb=100.0, entry_count=10)
    assert rep.total_size_mb == 100.0
    assert rep.entry_count == 10
