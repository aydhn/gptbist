import pytest
from bist_signal_bot.performance.reporting import cache_report_to_dict
from bist_signal_bot.performance.models import CacheReport

def test_cache_report_dict():
    rep = CacheReport(total_size_mb=5.5, entry_count=2)
    d = cache_report_to_dict(rep)
    assert d["total_size_mb"] == 5.5
    assert d["entry_count"] == 2
