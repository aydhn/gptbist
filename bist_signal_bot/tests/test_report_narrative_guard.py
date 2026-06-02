
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
