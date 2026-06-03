import pytest
from bist_signal_bot.maintenance_automation.reporting import format_maintenance_automation_report_markdown
from bist_signal_bot.maintenance_automation.models import MaintenanceAutomationReport
from datetime import datetime, timezone

def test_reporting_markdown_disclaimer():
    report = MaintenanceAutomationReport(
        report_id="1",
        generated_at=datetime.now(timezone.utc),
        disclaimer="Test disclaimer: not investment advice."
    )

    md_text = format_maintenance_automation_report_markdown(report)
    assert "not investment advice" in md_text
    assert "## Disclaimer" in md_text
