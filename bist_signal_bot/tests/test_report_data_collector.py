from bist_signal_bot.reports.collector import ReportDataCollector
from bist_signal_bot.reports.models import ReportConfig

def test_collector_returns_bundle():
    collector = ReportDataCollector()
    config = ReportConfig()
    bundle = collector.collect(config)
    assert bundle.report_type == config.report_type
    assert isinstance(bundle.source_summaries, dict)
