import pytest
from datetime import datetime, timezone
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.local_ui.models import LocalUIReport
from bist_signal_bot.local_ui.reporting import format_local_ui_report_markdown

def test_report_markdown_formatting():
    report = LocalUIReport(
        report_id="test_rep",
        generated_at=datetime.now(timezone.utc),
        key_findings=["Test finding"],
        warnings=["Test warning"]
    )
    md = format_local_ui_report_markdown(report)
    assert "# Local UI Report" in md
    assert "Test finding" in md
    assert "Test warning" in md
    assert "Disclaimer:" in md
