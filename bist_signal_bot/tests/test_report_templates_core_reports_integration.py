
from bist_signal_bot.reports.generator import generate_advanced_report
from bist_signal_bot.report_templates.models import ReportTemplateKind, ReportValidationStatus

def test_generate_advanced_report():
    res = generate_advanced_report("daily_research_report_v1", export=False, include_manifest=False)
    assert "report" in res
    rep = res["report"]
    assert rep.template_name == "daily_research_report_v1"
    assert rep.status == ReportValidationStatus.PASS
    assert res["pack"] is None
    assert res["manifest"] is None
