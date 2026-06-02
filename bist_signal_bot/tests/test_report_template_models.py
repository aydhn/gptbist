
import pytest
from bist_signal_bot.report_templates.models import ReportTemplate, ReportTemplateKind, ReportSectionDefinition, ReportSectionKind

def test_report_template_default_disclaimer():
    t = ReportTemplate(
        template_id="t1",
        name="test",
        kind=ReportTemplateKind.CUSTOM,
        version="1.0.0",
        description="desc"
    )
    assert "local software reporting metadata only" in t.disclaimer
    assert "not investment advice" in t.disclaimer

def test_report_section_order():
    s = ReportSectionDefinition(
        section_id="s1",
        section_key="key",
        title="title",
        kind=ReportSectionKind.SUMMARY,
        order=-1 # Order can technically be negative in pydantic unless we add a validator, but we test creation
    )
    assert s.order == -1
