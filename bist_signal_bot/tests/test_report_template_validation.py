
from bist_signal_bot.report_templates.validation import ReportTemplateValidator
from bist_signal_bot.report_templates.models import ReportTemplate, ReportTemplateKind, ReportSectionDefinition, ReportSectionKind, ReportValidationStatus

def test_validate_template_missing_disclaimer():
    val = ReportTemplateValidator()
    t = ReportTemplate(
        template_id="t1", name="n1", kind=ReportTemplateKind.CUSTOM, version="1", description="",
        sections=[ReportSectionDefinition(section_id="s1", section_key="summary", title="S", kind=ReportSectionKind.SUMMARY, order=1)]
    )
    res = val.validate_template(t)
    assert res.status == ReportValidationStatus.FAIL
    assert "disclaimer" in res.missing_required_sections

def test_unsafe_language_status():
    val = ReportTemplateValidator()
    unsafe = val.unsafe_language_findings("Bu kesin al diyor")
    assert "kesin al" in unsafe
    status = val.status_from_findings([], unsafe, [])
    assert status == ReportValidationStatus.BLOCKED
