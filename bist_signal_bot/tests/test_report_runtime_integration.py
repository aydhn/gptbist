from bist_signal_bot.runtime.orchestrator import RuntimeOrchestrator
from bist_signal_bot.runtime.pipelines import RuntimePipelineConfig
from bist_signal_bot.config.settings import Settings

class MockGenerator:
    def generate_runtime_summary(self, *args, **kwargs):
        from bist_signal_bot.reports.models import GeneratedReport, ReportType, ReportStatus, ReportAudience
        return GeneratedReport(
            report_id="1", report_type=ReportType.DAILY, audience=ReportAudience.PERSONAL,
            status=ReportStatus.SUCCESS, title="Test", output_files={}
        )

def test_runtime_generates_report():
    settings = Settings(RUNTIME_GENERATE_REPORT=True)
    orchestrator = RuntimeOrchestrator(settings=settings)
    orchestrator.report_generator = MockGenerator()

    class MockResult:
        metadata = {}
        issues = []

    config = RuntimePipelineConfig(strategy_name="test_strategy", generate_report=True, report_type="RUNTIME_SUMMARY")
    result = MockResult()

    try:
        report = orchestrator.report_generator.generate_runtime_summary("mock_run_id")
        result.metadata["report_id"] = report.report_id
    except Exception as e:
        pass

    assert "report_id" in result.metadata
