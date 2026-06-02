
from bist_signal_bot.report_templates.sections import ReportSectionLibrary
from bist_signal_bot.report_templates.models import ReportSectionDefinition, ReportSectionKind, ReportValidationStatus

def test_section_library_defaults():
    lib = ReportSectionLibrary()
    secs = lib.default_sections()
    assert len(secs) >= 4
    keys = [s.section_key for s in secs]
    assert "summary" in keys
    assert "disclaimer" in keys

def test_render_missing_renderer():
    lib = ReportSectionLibrary()
    s = ReportSectionDefinition(section_id="s1", section_key="test", title="Test", kind=ReportSectionKind.CUSTOM, order=1, renderer_name="nonexistent")
    res = lib.render_section(s, {})
    assert res.status == ReportValidationStatus.WATCH
    assert "Renderer nonexistent missing" in res.content_markdown
