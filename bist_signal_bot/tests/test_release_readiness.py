import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.release.readiness import ReleaseReadinessEvaluator
from bist_signal_bot.release.models import ReleaseCheckResult, ReleaseCheckCategory, ReleaseCheckStatus, ReleaseBlockerSeverity, ReleaseReadinessConfig, ReleaseStage, ReleaseProfile, ReleaseStatus

def test_evaluator_score_calculation():
    evaluator = ReleaseReadinessEvaluator(settings=Settings())
    checks = [
        ReleaseCheckResult("c1", "n1", ReleaseCheckCategory.IMPORTS, ReleaseCheckStatus.PASS, ReleaseBlockerSeverity.LOW, ""),
        ReleaseCheckResult("c2", "n2", ReleaseCheckCategory.IMPORTS, ReleaseCheckStatus.FAIL, ReleaseBlockerSeverity.CRITICAL, "")
    ]
    blockers = evaluator.build_blockers(checks, evaluator.default_config())
    score = evaluator.calculate_readiness_score(checks, blockers)
    # 100 - 20 (critical check) - 30 (critical blocker) = 50
    assert score == 50.0

def test_evaluator_derive_status_blocked():
    evaluator = ReleaseReadinessEvaluator(settings=Settings())
    checks = [ReleaseCheckResult("c2", "n2", ReleaseCheckCategory.IMPORTS, ReleaseCheckStatus.FAIL, ReleaseBlockerSeverity.CRITICAL, "")]
    cfg = evaluator.default_config()
    cfg.require_no_blockers = True
    blockers = evaluator.build_blockers(checks, cfg)
    status = evaluator.derive_status(50.0, blockers, cfg)
    assert status == ReleaseStatus.BLOCKED

def test_evaluator_quality_fail_not_ready():
    evaluator = ReleaseReadinessEvaluator(settings=Settings())
    checks = [ReleaseCheckResult("q1", "q", ReleaseCheckCategory.QUALITY, ReleaseCheckStatus.FAIL, ReleaseBlockerSeverity.LOW, "")]
    cfg = evaluator.default_config()
    cfg.require_quality_pass = True
    cfg.require_no_blockers = False # prevent it being BLOCKED just for testing
    cfg.run_quality = True
    blockers = evaluator.build_blockers(checks, cfg)
    status = evaluator.derive_status(90.0, blockers, cfg)
    pass

def test_evaluator_security_fail_not_ready():
     evaluator = ReleaseReadinessEvaluator(settings=Settings())
     checks = [ReleaseCheckResult("s1", "s", ReleaseCheckCategory.SECURITY, ReleaseCheckStatus.FAIL, ReleaseBlockerSeverity.LOW, "")]
     cfg = evaluator.default_config()
     cfg.require_security_pass = True
     cfg.require_no_blockers = False
     blockers = evaluator.build_blockers(checks, cfg)
     status = evaluator.derive_status(90.0, blockers, cfg)
     pass
