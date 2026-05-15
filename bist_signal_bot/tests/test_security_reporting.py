import pytest
from bist_signal_bot.security.reporting import (
    format_security_audit_text, format_kill_switch_status
)
from bist_signal_bot.security.models import (
    SecurityAuditReport, SecurityCheckStatus, KillSwitchState, KillSwitchScope
)

def test_format_security_audit_text():
    report = SecurityAuditReport(status=SecurityCheckStatus.PASS, overall_score=100.0)
    text = format_security_audit_text(report)
    assert "Overall Score: 100.0/100.0" in text
    assert "Status: PASS" in text

def test_format_kill_switch_status():
    state = KillSwitchState(enabled=True, scopes=[KillSwitchScope.RUNTIME], reason="Testing")
    text = format_kill_switch_status(state)
    assert "ACTIVE" in text
    assert "RUNTIME" in text
    assert "Testing" in text
