from bist_signal_bot.reports.templates import ReportTemplateRenderer
from bist_signal_bot.reports.models import GeneratedReport, ReportType, ReportStatus, ReportAudience, ReportSection, ReportSectionType

def test_render_markdown():
    report = GeneratedReport(
        report_id="1", report_type=ReportType.DAILY, audience=ReportAudience.PERSONAL,
        status=ReportStatus.SUCCESS, title="Test",
        sections=[ReportSection(section_id="1", section_type=ReportSectionType.CUSTOM, title="S1", body_markdown="body")]
    )
    renderer = ReportTemplateRenderer()
    md = renderer.render_markdown(report)
    assert "# Test" in md
    assert "## S1" in md
    assert "body" in md

def test_render_html():
    report = GeneratedReport(
        report_id="1", report_type=ReportType.DAILY, audience=ReportAudience.PERSONAL,
        status=ReportStatus.SUCCESS, title="Test",
        sections=[ReportSection(section_id="1", section_type=ReportSectionType.CUSTOM, title="S1", body_markdown="body")]
    )
    renderer = ReportTemplateRenderer()
    html = renderer.render_html(report)
    assert "<html><body><pre>" in html
    assert "# Test" in html

def test_render_json():
    report = GeneratedReport(
        report_id="1", report_type=ReportType.DAILY, audience=ReportAudience.PERSONAL,
        status=ReportStatus.SUCCESS, title="Test",
        sections=[ReportSection(section_id="1", section_type=ReportSectionType.CUSTOM, title="S1", body_markdown="body")]
    )
    renderer = ReportTemplateRenderer()
    d = renderer.render_json(report)
    assert d["title"] == "Test"
