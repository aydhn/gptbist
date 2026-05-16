import pytest
from bist_signal_bot.performance.recommendations import PerformanceRecommendationEngine
from bist_signal_bot.performance.models import ResourceSnapshot
from datetime import datetime, timezone

def test_resource_recommendations():
    engine = PerformanceRecommendationEngine()
    snap = ResourceSnapshot(timestamp=datetime.now(timezone.utc), memory_percent=85.0, disk_percent=90.0, cpu_count=2)

    recs = engine.recommend_from_resources(snap)
    assert len(recs) == 3
