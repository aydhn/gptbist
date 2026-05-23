import pytest
from bist_signal_bot.performance.reporting import format_performance_report_markdown
from bist_signal_bot.performance.models import BenchmarkRunResult, BenchmarkRequest, BenchmarkType, PerformanceStatus

def test_markdown_formatter():
    req = BenchmarkRequest(benchmark_type=BenchmarkType.SCANNER)
    bench = BenchmarkRunResult(benchmark_id="b1", request=req, status=PerformanceStatus.PASS)
    md = format_performance_report_markdown(bench)
    assert "Performance Report" in md
    assert "Operational only" in md.lower() or "not investment advice" in md.lower()
