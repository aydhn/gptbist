from pathlib import Path
from bist_signal_bot.reports.exporters import ReportExporter
from bist_signal_bot.reports.models import GeneratedReport, ReportType, ReportStatus, ReportAudience, ReportOutputFormat

def test_export_all_formats(tmp_path: Path):
    report = GeneratedReport(
        report_id="1", report_type=ReportType.DAILY, audience=ReportAudience.PERSONAL,
        status=ReportStatus.SUCCESS, title="Test"
    )
    exporter = ReportExporter()
    formats = [ReportOutputFormat.MARKDOWN, ReportOutputFormat.JSON, ReportOutputFormat.HTML, ReportOutputFormat.CSV, ReportOutputFormat.PDF]

    files = exporter.export(report, formats, tmp_path)

    assert "markdown" in files
    assert (tmp_path / "report.md").exists()

    assert "json" in files
    assert (tmp_path / "report.json").exists()

    assert "html" in files
    assert (tmp_path / "report.html").exists()

    # PDF is optional, might be None
    if "pdf" in files:
        assert files["pdf"] is None
