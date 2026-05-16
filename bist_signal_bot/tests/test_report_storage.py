from pathlib import Path
from bist_signal_bot.reports.storage import ReportStore
from bist_signal_bot.reports.models import GeneratedReport, ReportType, ReportStatus, ReportAudience, ReportOutputFormat
from bist_signal_bot.config.settings import Settings

def test_report_store_save(tmp_path: Path):
    settings = Settings(REPORTS_DIR_NAME="test_reports")
    store = ReportStore(settings=settings)
    report = GeneratedReport(
        report_id="1", report_type=ReportType.DAILY, audience=ReportAudience.PERSONAL,
        status=ReportStatus.SUCCESS, title="Test"
    )
    files = store.save_report(report, formats=[ReportOutputFormat.JSON], output_dir=tmp_path)
    assert "json" in files
    assert (tmp_path / "report.json").exists()
    assert (tmp_path / "metadata.json").exists()
