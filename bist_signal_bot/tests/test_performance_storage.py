import pytest
from bist_signal_bot.performance.storage import PerformanceReportStore
from bist_signal_bot.performance.models import CacheReport

def test_store_cache_report(tmp_path):
    store = PerformanceReportStore(base_dir=tmp_path)
    rep = CacheReport(total_size_mb=10)
    paths = store.save_cache_report(rep)

    assert "json" in paths
    assert paths["json"].exists()

def test_list_recent(tmp_path):
    store = PerformanceReportStore(base_dir=tmp_path)
    rep = CacheReport(total_size_mb=10)
    store.save_cache_report(rep)

    # cache report doesn't generate performance_result.json, we test that separately.
    assert isinstance(store.list_recent_performance_reports(), list)
