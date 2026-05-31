from bist_signal_bot.monitoring.reporting import format_monitoring_report_markdown
from bist_signal_bot.monitoring.models import MonitoringReport
from datetime import datetime

def test_reporting():
    rep = MonitoringReport(report_id="1", generated_at=datetime.now())
    txt = format_monitoring_report_markdown(rep)
    assert "Monitoring Report" in txt
    assert "not investment advice" in txt
