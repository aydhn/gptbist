from bist_signal_bot.config.settings import Settings
from bist_signal_bot.governance.models import GovernanceStatus, GovernanceDecision
from bist_signal_bot.governance.policy import GovernancePolicyManager
from bist_signal_bot.governance.rules import GovernanceRuleEvaluator

def test_evaluate_text_forbidden_pattern():
    mgr = GovernancePolicyManager(Settings())
    policy = mgr.default_policy()

    evaluator = GovernanceRuleEvaluator(Settings())

    # Safe text
    findings = evaluator.evaluate_text("This is a safe text. Not investment advice. No real order was sent.", policy)
    blocked = [f for f in findings if f.decision == GovernanceDecision.BLOCK]
    assert len(blocked) == 0

    # Unsafe text
    findings = evaluator.evaluate_text("Bu sistem size garanti kazanç sağlar ve gerçek order gönderir.", policy)
    blocked = [f for f in findings if f.decision == GovernanceDecision.BLOCK]
    assert len(blocked) > 0
    assert any("Forbidden pattern detected" in f.message for f in blocked)

def test_evaluate_text_secret_leak():
    mgr = GovernancePolicyManager(Settings())
    policy = mgr.default_policy()
    evaluator = GovernanceRuleEvaluator(Settings())

    # Text with a mock token
    unsafe_text = "Here is my api_key: 'abcdef1234567890abcdef1234567890' use it well."
    findings = evaluator.evaluate_text(unsafe_text, policy)

    secret_findings = [f for f in findings if f.title == "Rule: secret scan on outputs" and f.decision == GovernanceDecision.BLOCK]
    assert len(secret_findings) > 0

def test_evaluate_settings():
    class MockSettings(Settings):
        BROKER_API_ENABLED: bool = True

    settings = MockSettings()
    mgr = GovernancePolicyManager(settings)
    policy = mgr.default_policy()

    evaluator = GovernanceRuleEvaluator(settings)
    findings = evaluator.evaluate_settings(settings, policy)

    blocked = [f for f in findings if f.decision == GovernanceDecision.BLOCK]
    assert len(blocked) > 0
    assert any("BROKER_API_ENABLED" in f.message for f in blocked)
