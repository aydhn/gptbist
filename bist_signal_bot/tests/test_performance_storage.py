import pytest
from pathlib import Path
from datetime import datetime, UTC

from bist_signal_bot.performance.storage import PerformanceStore
from bist_signal_bot.performance.models import (
    PerformanceProfile,
    PerformanceStatus,
    BenchmarkResult,
    BenchmarkScenario,
    ResourceBudget
)

def test_performance_store_profiles(tmp_path):
    store = PerformanceStore(base_dir=tmp_path)

    p = PerformanceProfile(
        profile_id="p1",
        created_at=datetime.now(UTC),
        module_name="test_mod",
        timings=[],
        resources=[],
        cache_results=[],
        status=PerformanceStatus.PASS
    )

    store.append_profile(p)
    loaded = store.load_profiles()
    assert len(loaded) == 1
    assert loaded[0].profile_id == "p1"

    loaded_filtered = store.load_profiles(module_name="test_mod")
    assert len(loaded_filtered) == 1

    loaded_empty = store.load_profiles(module_name="other_mod")
    assert len(loaded_empty) == 0

def test_performance_store_benchmarks(tmp_path):
    store = PerformanceStore(base_dir=tmp_path)

    b = BenchmarkResult(
        benchmark_id="b1",
        scenario=BenchmarkScenario.ORCHESTRATOR_DRY_RUN,
        created_at=datetime.now(UTC),
        cache_hit_count=0,
        cache_miss_count=0,
        status=PerformanceStatus.PASS
    )

    store.append_benchmark(b)
    loaded = store.load_benchmarks()
    assert len(loaded) == 1
    assert loaded[0].benchmark_id == "b1"

def test_performance_store_budgets(tmp_path):
    store = PerformanceStore(base_dir=tmp_path)

    budget = ResourceBudget(
        budget_id="bdg1",
        module_name="test",
        status=PerformanceStatus.PASS
    )

    store.save_budgets([budget])
    loaded = store.load_budgets()

    assert len(loaded) == 1
    assert loaded[0].budget_id == "bdg1"

