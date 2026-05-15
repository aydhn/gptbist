from datetime import datetime, timezone
from bist_signal_bot.security.models import (
    SecurityCheckResult, SecurityComponent, SecurityCheckStatus, SecurityLevel,
    KillSwitchState, KillSwitchScope, SecurityAuditReport
)

def test_security_check_result_summary():
    result = SecurityCheckResult(
        check_name="test_check",
        component=SecurityComponent.CONFIG,
        status=SecurityCheckStatus.PASS,
        severity=SecurityLevel.HIGH,
        message="Test message",
        recommendations=["Do nothing"]
    )
    summary = result.summary()
    assert summary["check_name"] == "test_check"
    assert summary["component"] == "CONFIG"
    assert summary["status"] == "PASS"
    assert summary["severity"] == "HIGH"
    assert summary["message"] == "Test message"
    assert summary["recommendations"] == ["Do nothing"]

def test_kill_switch_state_scope_checking():
    # Active for ALL
    state1 = KillSwitchState(enabled=True, scopes=[KillSwitchScope.ALL])
    assert state1.is_active_for(KillSwitchScope.RUNTIME) is True
    assert state1.is_active_for(KillSwitchScope.PAPER) is True

    # Active for specific
    state2 = KillSwitchState(enabled=True, scopes=[KillSwitchScope.PAPER])
    assert state2.is_active_for(KillSwitchScope.PAPER) is True
    assert state2.is_active_for(KillSwitchScope.RUNTIME) is False

    # Disabled
    state3 = KillSwitchState(enabled=False, scopes=[KillSwitchScope.ALL])
    assert state3.is_active_for(KillSwitchScope.RUNTIME) is False

def test_security_audit_report_summaries():
    report = SecurityAuditReport(
        status=SecurityCheckStatus.PASS,
        overall_score=95.0,
        checks=[],
        secret_findings=[],
        forbidden_action_findings=[],
    )
    summary = report.summary()
    assert summary["status"] == "PASS"
    assert summary["overall_score"] == 95.0
    assert summary["check_count"] == 0
    assert summary["secret_findings_count"] == 0
    assert summary["forbidden_action_findings_count"] == 0
    assert summary["kill_switch_active"] is False

    safe_dict = report.safe_public_dict()
    assert safe_dict["issues_found"] == 0
    assert "disclaimer" in safe_dict
