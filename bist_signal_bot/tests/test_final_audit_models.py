import pytest
from bist_signal_bot.final_audit.models import (
    FinalAuditCheckResult,
    FinalAcceptanceSuite,
    FinalSecurityAuditResult,
    ReleaseCandidateManifest,
    GoNoGoDecision,
    FinalCheckType,
    FinalAuditStatus,
    ReleaseDecision
)
from datetime import datetime, timezone

def test_final_audit_check_result_validation():
    now = datetime.now(timezone.utc)
    res = FinalAuditCheckResult(
        check_id="chk_1",
        check_type=FinalCheckType.IMPORT_CHECK,
        module_name="core",
        name="Import core",
        status=FinalAuditStatus.PASS,
        started_at=now
    )
    assert res.status == FinalAuditStatus.PASS

def test_final_acceptance_suite_counts():
    now = datetime.now(timezone.utc)
    suite = FinalAcceptanceSuite(
        suite_id="acc_1",
        created_at=now,
        name="Test",
        total_count=10,
        pass_count=8,
        fail_count=2
    )
    assert suite.pass_count == 8
    assert "local software QA metadata only" in suite.disclaimer

def test_release_candidate_manifest_limitations():
    now = datetime.now(timezone.utc)
    cand = ReleaseCandidateManifest(
        candidate_id="rc_1",
        created_at=now,
        known_limitations=["No real broker integration"]
    )
    assert "No real broker integration" in cand.known_limitations
    assert "investment advice" in cand.disclaimer

def test_go_no_go_decision_trade_readiness_language_missing():
    now = datetime.now(timezone.utc)
    dec = GoNoGoDecision(
        decision_id="gn_1",
        candidate_id="rc_1",
        created_at=now,
        decision=ReleaseDecision.GO,
        status=FinalAuditStatus.PASS,
        final_notes=["Review completed."]
    )
    assert "trade ready" not in " ".join(dec.final_notes).lower()
