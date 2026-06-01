import pytest
from datetime import datetime, UTC
from bist_signal_bot.performance.reporting import format_performance_report_markdown
from bist_signal_bot.performance.models import PerformanceReport

def test_reporting_markdown_disclaimer():
    report = PerformanceReport(
        report_id="r1",
        generated_at=datetime.now(UTC),
        profiles=[],
        benchmarks=[],
        bottlenecks=[],
        regressions=[],
        resource_budgets=[],
        cache_entries=[],
        key_findings=["All good"]
    )

    md = format_performance_report_markdown(report)
    assert "Disclaimer" in md
    assert "local software optimization reporting only" in md
    assert "All good" in md

