from bist_signal_bot.config.settings import Settings
from bist_signal_bot.governance.models import AuditReviewRequest, GovernanceStatus
from bist_signal_bot.governance.audit_review import AuditReviewEngine, AuditReviewDependencies
from bist_signal_bot.governance.policy import GovernancePolicyManager
from bist_signal_bot.governance.rules import GovernanceRuleEvaluator

def test_audit_review_engine_no_findings(tmp_path):
    class MockSettings(Settings):
        BROKER_API_ENABLED: bool = False
        PAID_API_ENABLED: bool = False
        HTML_SCRAPING_ENABLED: bool = False
        GOVERNANCE_WARN_ON_MISSING_DISCLAIMER: bool = True
        GOVERNANCE_REQUIRE_RESEARCH_ONLY: bool = True
        GOVERNANCE_BLOCK_REAL_ORDER_LANGUAGE: bool = True
        GOVERNANCE_BLOCK_BROKER_API: bool = True
        GOVERNANCE_BLOCK_PAID_SERVICES: bool = True
        GOVERNANCE_BLOCK_HTML_SCRAPING: bool = True
        GOVERNANCE_REQUIRE_SECRET_REDACTION: bool = True
        GOVERNANCE_REQUIRE_CONFIRM_FOR_POLICY_UPDATE: bool = True

    settings = MockSettings()
    deps = AuditReviewDependencies(
        policy_manager=GovernancePolicyManager(settings),
        rule_evaluator=GovernanceRuleEvaluator(settings),
        settings=settings,
        base_dir=tmp_path
    )
    engine = AuditReviewEngine(deps=deps)

    request = AuditReviewRequest(save_output=False)
    result = engine.review(request)

    # Since we don't have broken settings, it should pass
    assert result.status == GovernanceStatus.PASS
    assert result.blocked_count == 0

def test_audit_review_engine_with_findings(tmp_path):
    class MockSettings(Settings):
        BROKER_API_ENABLED: bool = True # This will trigger a block
        GOVERNANCE_WARN_ON_MISSING_DISCLAIMER: bool = True
        GOVERNANCE_REQUIRE_RESEARCH_ONLY: bool = True
        GOVERNANCE_BLOCK_REAL_ORDER_LANGUAGE: bool = True
        GOVERNANCE_BLOCK_BROKER_API: bool = True
        GOVERNANCE_BLOCK_PAID_SERVICES: bool = True
        GOVERNANCE_BLOCK_HTML_SCRAPING: bool = True
        GOVERNANCE_REQUIRE_SECRET_REDACTION: bool = True
        GOVERNANCE_REQUIRE_CONFIRM_FOR_POLICY_UPDATE: bool = True

    settings = MockSettings()
    deps = AuditReviewDependencies(
        policy_manager=GovernancePolicyManager(settings),
        rule_evaluator=GovernanceRuleEvaluator(settings),
        settings=settings,
        base_dir=tmp_path
    )
    engine = AuditReviewEngine(deps=deps)

    request = AuditReviewRequest(save_output=False)
    result = engine.review(request)

    assert result.status == GovernanceStatus.BLOCKED
    assert result.blocked_count > 0
