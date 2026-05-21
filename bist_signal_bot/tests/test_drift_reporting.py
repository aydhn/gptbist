import pytest
from bist_signal_bot.drift.models import DriftAnalysisResult, DriftAnalysisRequest
from bist_signal_bot.drift.reporting import format_drift_report_markdown

def test_markdown_formatting():
    req = DriftAnalysisRequest()
    res = DriftAnalysisResult(drift_id="test_id_123", request=req, warnings=["Test warning"])

    md = format_drift_report_markdown(res)
    assert "Drift Analysis Report" in md
    assert "test_id_123" in md
    assert "Disclaimer" in md
    assert "research-only" in md
    assert "Test warning" in md
