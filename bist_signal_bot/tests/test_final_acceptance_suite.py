import pytest
from bist_signal_bot.final_audit.acceptance import FinalAcceptanceSuiteRunner
from bist_signal_bot.final_audit.models import FinalAuditStatus, FinalAuditCheckResult, FinalCheckType
from datetime import datetime, timezone

def test_acceptance_suite_runner_counts_and_status():
    runner = FinalAcceptanceSuiteRunner()
    suite = runner.run_acceptance_suite()
    assert suite.total_count == suite.pass_count + suite.watch_count + suite.fail_count + suite.blocked_count
    assert suite.status == FinalAuditStatus.PASS

def test_classify_suite():
    runner = FinalAcceptanceSuiteRunner()
    now = datetime.now(timezone.utc)
    c1 = FinalAuditCheckResult(
        check_id="1", check_type=FinalCheckType.ACCEPTANCE,
        module_name="a", name="a", status=FinalAuditStatus.PASS, started_at=now
    )
    c2 = FinalAuditCheckResult(
        check_id="2", check_type=FinalCheckType.ACCEPTANCE,
        module_name="b", name="b", status=FinalAuditStatus.BLOCKED, started_at=now
    )

    assert runner.classify_suite([c1]) == FinalAuditStatus.PASS
    assert runner.classify_suite([c1, c2]) == FinalAuditStatus.BLOCKED
