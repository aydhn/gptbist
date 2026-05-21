from bist_signal_bot.governance.models import (
    GovernanceRule,
    GovernanceDomain,
    GovernanceRuleType,
    GovernanceSeverity,
    GovernancePolicy
)

def test_governance_rule_instantiation():
    rule = GovernanceRule(
        rule_id="test_1",
        name="Test Rule",
        domain=GovernanceDomain.RESEARCH_ONLY,
        rule_type=GovernanceRuleType.REQUIRED_DISCLAIMER,
        severity=GovernanceSeverity.HIGH,
        description="A test rule",
    )
    assert rule.rule_id == "test_1"
    assert rule.enabled is True
    assert rule.blocking is False

def test_governance_policy_instantiation():
    policy = GovernancePolicy(
        policy_id="pol_1",
        version="1.0.0",
    )
    assert policy.require_research_only is True
    assert policy.block_broker_api is True
