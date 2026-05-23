import pytest
from bist_signal_bot.performance.bottlenecks import BottleneckAnalyzer
from bist_signal_bot.performance.models import ProfileResult, BenchmarkType, ProfileSpan
import datetime

def test_bottleneck_slow_spans():
    analyzer = BottleneckAnalyzer()
    now = datetime.datetime.now(datetime.timezone.utc)
    s1 = ProfileSpan(span_id="1", name="s1", started_at=now, elapsed_seconds=0.1)
    s2 = ProfileSpan(span_id="2", name="s2", started_at=now, elapsed_seconds=5.0) # Slow
    prof = ProfileResult(profile_id="p1", benchmark_type=BenchmarkType.CUSTOM, started_at=now, spans=[s1, s2])

    findings = analyzer.analyze_profile(prof)
    assert len(findings) == 1
    assert "Slow execution" in findings[0].name
