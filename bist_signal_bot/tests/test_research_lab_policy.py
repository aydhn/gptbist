import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.research_lab.policy import ResearchLabPolicyManager
from bist_signal_bot.research_lab.models import ResearchLabPolicy
from bist_signal_bot.core.exceptions import ResearchLabValidationError

def test_policy_defaults():
    mgr = ResearchLabPolicyManager(Settings())
    pol = mgr.default_policy()
    assert pol.max_jobs_per_batch > 0
    assert pol.allow_network is False

def test_policy_validation_failure():
    mgr = ResearchLabPolicyManager(Settings())
    pol = mgr.default_policy()
    pol.max_jobs_per_batch = -1
    with pytest.raises(ResearchLabValidationError):
        mgr.validate_policy(pol)

def test_policy_save_requires_confirm(tmp_path):
    mgr = ResearchLabPolicyManager(Settings())
    pol = mgr.default_policy()
    with pytest.raises(ResearchLabValidationError):
         mgr.save_policy(pol, path=tmp_path / "pol.json", confirm=False)
