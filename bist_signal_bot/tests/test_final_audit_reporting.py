import pytest
from datetime import datetime, timezone
from bist_signal_bot.final_audit.reporting import format_final_audit_report_markdown, format_risk_register_text
from bist_signal_bot.final_audit.models import FinalAuditReport, FinalRiskRegisterItem

def test_reporting_markdown_disclaimer():
    now = datetime.now(timezone.utc)
    report = FinalAuditReport(report_id="rpt_1", generated_at=now)

    md = format_final_audit_report_markdown(report)
    assert "No real order was sent" in md


def test_format_risk_register_text():
    items = [
        FinalRiskRegisterItem(risk_id="R1", title="Risk 1", description="Desc 1", severity="HIGH", accepted=False),
        FinalRiskRegisterItem(risk_id="R2", title="Risk 2", description="Desc 2", severity="LOW", accepted=True),
    ]
    formatted = format_risk_register_text(items)

    assert "Final Risk Register:" in formatted
    assert "[HIGH] Risk 1: Desc 1 (Accepted: False)" in formatted
    assert "[LOW] Risk 2: Desc 2 (Accepted: True)" in formatted
