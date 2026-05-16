from bist_signal_bot.reports.generator import ResearchReportGenerator
from bist_signal_bot.reports.models import ReportType

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
