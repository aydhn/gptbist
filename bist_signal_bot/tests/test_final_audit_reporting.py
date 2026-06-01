import pytest
from datetime import datetime, timezone
from bist_signal_bot.final_audit.reporting import format_final_audit_report_markdown
from bist_signal_bot.final_audit.models import FinalAuditReport

def test_reporting_markdown_disclaimer():
    now = datetime.now(timezone.utc)
    report = FinalAuditReport(report_id="rpt_1", generated_at=now)

    md = format_final_audit_report_markdown(report)
    assert "No real order was sent" in md
