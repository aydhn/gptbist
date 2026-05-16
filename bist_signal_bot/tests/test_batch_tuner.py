import pytest
from bist_signal_bot.performance.batch import BatchTuner
from bist_signal_bot.performance.models import ResourceSnapshot, WorkloadType, ConcurrencyMode
from datetime import datetime, timezone
from bist_signal_bot.config.settings import Settings

def test_batch_tuner_safe_workers():
    s = Settings()
    s.PERFORMANCE_MAX_WORKERS = 4
    tuner = BatchTuner(s)
    w = tuner.safe_max_workers(8, 8000)
    assert w > 1
    w2 = tuner.safe_max_workers(2, 500)
    assert w2 == 1

def test_batch_tuner_memory_constrained():
    settings = Settings()
    settings.PERFORMANCE_MEMORY_WARN_PCT = 80.0
    tuner = BatchTuner(settings)

    snap = ResourceSnapshot(timestamp=datetime.now(timezone.utc), cpu_count=8, memory_percent=90.0)
    rec = tuner.recommend_for_workload(WorkloadType.SCANNER, snap, 100)

    assert rec.recommended_max_workers == 1
    assert len(rec.warnings) > 0

def test_chunk_symbols():
    s = Settings()
    s.PERFORMANCE_MAX_WORKERS = 4
    tuner = BatchTuner(s)
    chunks = tuner.chunk_symbols(["A", "B", "C", "D"], 2)
    assert len(chunks) == 2
    assert chunks[0] == ["A", "B"]
