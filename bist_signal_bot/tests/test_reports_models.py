import pytest
from datetime import datetime
from bist_signal_bot.reports.models import ReportConfig, ReportSection, ReportSectionType, GeneratedReport, ReportType, ReportStatus, ReportAudience

def test_report_config_validation():
    # Valid
    config = ReportConfig(top_n=5)
    assert config.top_n == 5

    # Invalid top_n
    with pytest.raises(ValueError):
        ReportConfig(top_n=0)

    # Invalid dates
    with pytest.raises(ValueError):
        ReportConfig(start_date=datetime(2023, 1, 2), end_date=datetime(2023, 1, 1))

def test_report_section_validation():
    with pytest.raises(ValueError):
        ReportSection(section_id="test", section_type=ReportSectionType.CUSTOM, title=" ", body_markdown="body")

def test_generated_report_summary():
    report = GeneratedReport(
        report_id="TEST-1",
        report_type=ReportType.DAILY,
        audience=ReportAudience.PERSONAL,
        status=ReportStatus.SUCCESS,
        title="Test Report"
    )
    summary = report.summary()
    assert summary["report_id"] == "TEST-1"
    assert summary["status"] == "SUCCESS"
