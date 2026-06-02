import os
from pathlib import Path

# test_report_template_models.py
Path("bist_signal_bot/tests/test_report_template_models.py").write_text('''
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
''')

# test_report_template_library.py
Path("bist_signal_bot/tests/test_report_template_library.py").write_text('''
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
''')

# test_report_sections_library.py
Path("bist_signal_bot/tests/test_report_sections_library.py").write_text('''
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
''')

# test_report_composer.py
Path("bist_signal_bot/tests/test_report_composer.py").write_text('''
import pytest
from bist_signal_bot.report_templates.composer import ReportComposer
from bist_signal_bot.core.exceptions import ReportComposerError
from bist_signal_bot.report_templates.models import ReportValidationStatus

def test_compose_not_found():
    composer = ReportComposer()
    with pytest.raises(ReportComposerError):
        composer.compose("nonexistent_template_xyz")

def test_compose_daily_template():
    composer = ReportComposer()
    report = composer.compose("daily_research_report_v1")
    assert report.template_name == "daily_research_report_v1"
    assert report.status == ReportValidationStatus.PASS
    keys = [s.section_key for s in report.sections]
    assert "summary" in keys
    assert "disclaimer" in keys
    assert report.markdown_text is not None
    assert "Executive Summary" in report.markdown_text
    assert isinstance(report.json_payload, dict)

def test_compose_missing_context_generates_default():
    composer = ReportComposer()
    report = composer.compose("daily_research_report_v1", context=None)
    summary_sec = next(s for s in report.sections if s.section_key == "summary")
    assert "Auto-generated context" in summary_sec.content_markdown
''')

# test_report_narrative_guard.py
Path("bist_signal_bot/tests/test_report_narrative_guard.py").write_text('''
from bist_signal_bot.report_templates.narrative import ReportNarrativeGuard
from bist_signal_bot.report_templates.models import ReportValidationStatus

def test_detect_unsafe_language():
    guard = ReportNarrativeGuard()
    findings = guard.detect_unsafe_language("Bu hisseyi kesin almalısınız, hedef fiyat 100.")
    assert "kesin al" in findings
    assert "hedef fiyat" in findings

def test_build_safe_narrative():
    guard = ReportNarrativeGuard()
    block = guard.build_narrative_block("Title", "Piyasa genel olarak yatay seyrediyor.")
    assert block.safe_language_status == ReportValidationStatus.PASS
    assert not block.warnings

def test_build_unsafe_narrative():
    guard = ReportNarrativeGuard()
    block = guard.build_narrative_block("Title", "Buradan kesin sat trade ready.")
    assert block.safe_language_status == ReportValidationStatus.BLOCKED
    assert len(block.warnings) > 0
    assert "[REDACTED]" in block.text
''')

print("Phase 103 Part 11 test files generated.")
