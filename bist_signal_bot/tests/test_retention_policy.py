import pytest
from bist_signal_bot.maintenance.retention import RetentionPolicyManager
from bist_signal_bot.maintenance.models import RetentionTarget

def test_retention_default_policies():
    policies = RetentionPolicyManager.default_policies()
    assert len(policies) > 0

    logs_policy = next(p for p in policies if p.target == RetentionTarget.LOGS)
    assert logs_policy.keep_days > 0

def test_policy_for_target():
    policy = RetentionPolicyManager.policy_for_target(RetentionTarget.TEMP)
    assert policy.target == RetentionTarget.TEMP
    assert policy.keep_days > 0
