import pytest
from bist_signal_bot.final_audit.contracts import FinalContractAuditor
from bist_signal_bot.final_audit.models import FinalAuditStatus

def test_contract_auditor_all_pass():
    auditor = FinalContractAuditor()
    results = auditor.audit_contracts()

    assert len(results) == 6
    assert all(r.status == FinalAuditStatus.PASS for r in results)

def test_contract_drift_detected():
    auditor = FinalContractAuditor()
    res = auditor.detect_contract_drift()
    assert res.status == FinalAuditStatus.PASS
