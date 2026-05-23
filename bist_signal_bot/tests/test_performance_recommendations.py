import pytest
from bist_signal_bot.performance.recommendations import PerformanceRecommendationEngine
from bist_signal_bot.performance.models import BottleneckFinding, BenchmarkType, PerformanceSeverity

def test_recommendation_from_findings():
    engine = PerformanceRecommendationEngine()
    f1 = BottleneckFinding(finding_id="1", name="High memory growth in X", benchmark_type=BenchmarkType.CUSTOM, severity=PerformanceSeverity.HIGH, message="test")
    recs = engine.recommend([f1])
    assert len(recs) == 1
    assert "memory footprint" in recs[0].title.lower()
