import pytest
from bist_signal_bot.final_audit.checks import FinalAuditCheckRunner
from bist_signal_bot.final_audit.acceptance import FinalAcceptanceSuiteRunner
from bist_signal_bot.final_audit.models import FinalAuditStatus

def test_check_runner_import_checks_deterministic():
    runner = FinalAuditCheckRunner()
    results = runner.run_import_checks()

    assert len(results) > 0
    # Core should pass
    core_res = next(r for r in results if r.module_name == "core")
    assert core_res.status == FinalAuditStatus.PASS

def test_acceptance_suite_runner_critical_checks():
    runner = FinalAcceptanceSuiteRunner()
    checks = runner.critical_acceptance_checks()
    assert len(checks) > 0
    assert any(c.module_name == "bootstrap" for c in checks)

def test_acceptance_suite_runner_orchestrator_dry_run_mocked():
    runner = FinalAcceptanceSuiteRunner()
    check = runner.run_orchestrator_dry_run_acceptance()
    assert check.status == FinalAuditStatus.PASS
    assert check.module_name == "research_orchestrator"
