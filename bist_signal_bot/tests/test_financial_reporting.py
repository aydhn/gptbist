import pytest
from datetime import datetime
from bist_signal_bot.financials.reporting import format_financial_analysis_report_markdown
from bist_signal_bot.financials.models import FinancialAnalysisReport

def test_report_formatting():
    rep = FinancialAnalysisReport(
        report_id="1",
        symbol="ASELS",
        generated_at=datetime.now(),
        normalized_statements=[],
        ratios=[],
        trends=[],
        quality_assessments=[],
        sector_comparisons=[],
        key_findings=["Finding 1"],
        warnings=[],
        metadata={}
    )
    md = format_financial_analysis_report_markdown(rep)
    assert "Financial Analysis Report" in md
    assert "Finding 1" in md
    assert "research-only. It is not investment advice" in md
