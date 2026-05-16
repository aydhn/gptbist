from bist_signal_bot.reports.sections import ReportSectionBuilder
from bist_signal_bot.reports.models import ReportConfig, ReportDataBundle, ReportType

def test_build_disclaimer():
    builder = ReportSectionBuilder()
    config = ReportConfig()
    section = builder.build_disclaimer_section(config)
    assert section.title == "Disclaimer"
    assert "Not investment advice" in section.body_markdown

def test_build_executive_summary():
    builder = ReportSectionBuilder()
    bundle = ReportDataBundle(report_type=ReportType.DAILY)
    config = ReportConfig()
    section = builder.build_executive_summary(bundle, config)
    assert section.title == "Executive Summary"
