import pytest
from bist_signal_bot.final_audit.security_audit import FinalSecurityAuditor
from bist_signal_bot.final_audit.models import FinalAuditStatus

def test_security_auditor_all_pass():
    auditor = FinalSecurityAuditor()
    res = auditor.run_security_audit()
    assert res.safe_language_status == FinalAuditStatus.PASS
    assert res.no_broker_status == FinalAuditStatus.PASS
    assert not res.blocked_findings
