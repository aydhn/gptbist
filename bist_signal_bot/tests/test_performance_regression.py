import pytest
from datetime import datetime, UTC
import uuid

from bist_signal_bot.performance.regression import PerformanceRegressionDetector
from bist_signal_bot.performance.models import (
    BenchmarkResult,
    BenchmarkScenario,
    PerformanceStatus
)

def test_regression_baseline_missing():
    detector = PerformanceRegressionDetector()
    detector.baseline_required = False

    current = [
        BenchmarkResult(
            benchmark_id="b1",
            scenario=BenchmarkScenario.ORCHESTRATOR_DRY_RUN,
            created_at=datetime.now(UTC),
            cache_hit_count=0,
            cache_miss_count=0,
            status=PerformanceStatus.PASS
        )
    ]

    findings = detector.detect_regressions(current, baseline=None)
    assert len(findings) == 1
    assert findings[0].status == PerformanceStatus.WATCH

def test_regression_delta_pct():
    detector = PerformanceRegressionDetector()

    assert detector.delta_pct(150.0, 100.0) == 50.0
    assert detector.delta_pct(90.0, 100.0) == -10.0
    assert detector.delta_pct(None, 100.0) is None

def test_regression_finding_generation():
    detector = PerformanceRegressionDetector()

    c = BenchmarkResult(
        benchmark_id="c1",
        scenario=BenchmarkScenario.ORCHESTRATOR_DRY_RUN,
        created_at=datetime.now(UTC),
        cache_hit_count=0,
        cache_miss_count=0,
        status=PerformanceStatus.PASS,
        elapsed_seconds=160.0
    )
    b = BenchmarkResult(
        benchmark_id="b1",
        scenario=BenchmarkScenario.ORCHESTRATOR_DRY_RUN,
        created_at=datetime.now(UTC),
        cache_hit_count=0,
        cache_miss_count=0,
        status=PerformanceStatus.PASS,
        elapsed_seconds=100.0
    )

    finding = detector.compare_result(c, b)
    assert finding.delta_pct == 60.0
    assert finding.status == PerformanceStatus.FAIL

