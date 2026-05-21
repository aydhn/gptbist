import pytest
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.governance.policy import GovernancePolicyManager
from bist_signal_bot.core.exceptions import GovernancePolicyError

def test_default_policy():
    mgr = GovernancePolicyManager(Settings())
    policy = mgr.default_policy()
    assert policy is not None
    assert len(policy.rules) > 0

    # Check default rules
    rule_names = [r.name for r in policy.rules]
    assert "no_real_order_sent disclaimer required" in rule_names

def test_save_policy_requires_confirm(tmp_path):
    mgr = GovernancePolicyManager(Settings())
    policy = mgr.default_policy()

    with pytest.raises(GovernancePolicyError, match="requires explicit confirmation"):
        mgr.save_policy(policy, path=tmp_path / "policy.json", confirm=False)

def test_save_and_load_policy(tmp_path):
    mgr = GovernancePolicyManager(Settings())
    policy = mgr.default_policy()

    path = tmp_path / "policy.json"
    mgr.save_policy(policy, path=path, confirm=True)

    assert path.exists()

    loaded = mgr.load_policy(path)
    assert loaded.policy_id == policy.policy_id

def test_policy_no_secrets_in_rules():
    mgr = GovernancePolicyManager(Settings())
    policy = mgr.default_policy()

    # Inject a secret rule
    policy.rules[0].expected_setting = "MY_SECRET_TOKEN"
    policy.rules[0].expected_value = "super_secret_value_123"

    with pytest.raises(GovernancePolicyError, match="cannot contain plaintext secrets"):
        mgr.validate_policy(policy)
