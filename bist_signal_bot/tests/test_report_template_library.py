
from bist_signal_bot.report_templates.library import ReportTemplateLibrary
from bist_signal_bot.report_templates.models import ReportTemplateKind, ReportTemplate, ReportSectionDefinition, ReportSectionKind

def test_template_library_defaults():
    lib = ReportTemplateLibrary()
    templates = lib.default_templates()
    assert len(templates) >= 13
    assert any(t.kind == ReportTemplateKind.DAILY for t in templates)

def test_validate_template_duplicate_section():
    lib = ReportTemplateLibrary()
    t = ReportTemplate(
        template_id="t1",
        name="test",
        kind=ReportTemplateKind.CUSTOM,
        version="1.0",
        description="desc",
        sections=[
            ReportSectionDefinition(section_id="s1", section_key="dup", title="T1", kind=ReportSectionKind.CUSTOM, order=1),
            ReportSectionDefinition(section_id="s2", section_key="dup", title="T2", kind=ReportSectionKind.CUSTOM, order=2),
            ReportSectionDefinition(section_id="s3", section_key="disclaimer", title="Disc", kind=ReportSectionKind.DISCLAIMER, order=3)
        ]
    )
    findings = lib.validate_template(t)
    assert any("Duplicate section_key" in f for f in findings)
