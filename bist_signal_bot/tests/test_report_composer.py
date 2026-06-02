
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
