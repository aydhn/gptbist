import pytest
from bist_signal_bot.data_import.reporting import format_data_import_report_markdown
from bist_signal_bot.data_import.models import DataImportReport
from datetime import datetime, timezone

def test_format_report_disclaimer():
    report = DataImportReport(
        report_id="r1",
        generated_at=datetime.now(timezone.utc)
    )
    md = format_data_import_report_markdown(report)
    assert "not investment advice" in md.lower()
