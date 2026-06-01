import pytest
from bist_signal_bot.final_handoff.reporting import format_final_handoff_report_markdown
from bist_signal_bot.final_handoff.models import FinalHandoffReport
from datetime import datetime

def test_reporting_markdown_disclaimer():
    report = FinalHandoffReport(
        report_id="r1",
        generated_at=datetime.now()
    )
    md = format_final_handoff_report_markdown(report)
    assert "not investment advice" in md
