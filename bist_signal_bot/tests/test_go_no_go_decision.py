import pytest
from bist_signal_bot.final_audit.go_no_go import GoNoGoEvaluator
from bist_signal_bot.final_audit.release_candidate import ReleaseCandidateBuilder
from bist_signal_bot.final_audit.acceptance import FinalAcceptanceSuiteRunner
from bist_signal_bot.final_audit.security_audit import FinalSecurityAuditor
from bist_signal_bot.final_audit.models import FinalAuditStatus, ReleaseDecision

def test_go_no_go_evaluator_all_pass():
    evaluator = GoNoGoEvaluator()
    builder = ReleaseCandidateBuilder()
    cand = builder.build_candidate()
    acc = FinalAcceptanceSuiteRunner().run_acceptance_suite()
    sec = FinalSecurityAuditor().run_security_audit()

    decision = evaluator.evaluate(cand, acc, sec, None)
    assert decision.decision == ReleaseDecision.GO

def test_go_no_go_security_blocked():
    evaluator = GoNoGoEvaluator()
    builder = ReleaseCandidateBuilder()
    cand = builder.build_candidate()
    sec = FinalSecurityAuditor().run_security_audit()
    sec.blocked_findings = ["Unsafe broker call"]

    decision = evaluator.evaluate(cand, None, sec, None)
    assert decision.decision == ReleaseDecision.BLOCKED

def test_go_no_go_validate():
    evaluator = GoNoGoEvaluator()
    builder = ReleaseCandidateBuilder()
    cand = builder.build_candidate()
    dec = evaluator.evaluate(cand, None, None, None)

    dec.final_notes = ["This is trade ready."]
    errors = evaluator.validate_decision(dec)
    assert len(errors) == 1
    assert "trade readiness" in errors[0]
