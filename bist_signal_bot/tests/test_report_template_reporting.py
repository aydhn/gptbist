
from bist_signal_bot.report_templates.reporting import format_template_text, format_composed_report_text
from bist_signal_bot.report_templates.models import ReportTemplate, ReportTemplateKind, ComposedReport
from datetime import datetime

def test_format_template_text():
    t = ReportTemplate(template_id="t1", name="test_tmpl", kind=ReportTemplateKind.CUSTOM, version="1", description="")
    out = format_template_text(t)
    assert "test_tmpl" in out
    assert "CUSTOM" in out

def test_format_composed_report_text():
    r = ComposedReport(report_id="r1", template_id="t1", template_name="test_tmpl", kind=ReportTemplateKind.CUSTOM, generated_at=datetime.utcnow())
    out = format_composed_report_text(r)
    assert "r1" in out
    assert "test_tmpl" in out
    assert "local research software output only" in out
