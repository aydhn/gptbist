import pytest
from bist_signal_bot.research_orchestrator.reporting import format_orchestrator_report_markdown
from bist_signal_bot.research_orchestrator.models import ResearchOrchestratorReport
from datetime import datetime, timezone

def test_reporting_disclaimer():
    report = ResearchOrchestratorReport(
        report_id="rep1", generated_at=datetime.now(timezone.utc)
    )
    md = format_orchestrator_report_markdown(report)
    assert "Disclaimer" in md
    assert report.disclaimer in md
    assert "Research Orchestrator Report" in md
