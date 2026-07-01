from bist_signal_bot.reports.generator import ResearchReportGenerator
from bist_signal_bot.reports.models import ReportType, ReportStatus

class MockStorage:
    def save_report(self, report, formats):
        pass

def test_generate_daily():
    generator = ResearchReportGenerator(storage=MockStorage())
    report = generator.generate_daily(save_report=True)
    assert report.report_type == ReportType.DAILY
    assert "BIST Research Report" in report.title

def test_generate_weekly():
    generator = ResearchReportGenerator(storage=MockStorage())
    report = generator.generate_weekly()
    assert report.report_type == ReportType.WEEKLY


class MockCollectorWithError:
    def collect(self, config):
        raise ValueError("Simulated collection error")

def test_generate_error_handling():
    generator = ResearchReportGenerator(
        storage=MockStorage(),
        collector=MockCollectorWithError()
    )
    report = generator.generate_daily(save_report=False)
    assert report.status == ReportStatus.FAILED
    assert report.issues is not None
    assert "Simulated collection error" in report.issues[0]
