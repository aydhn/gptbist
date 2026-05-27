import pytest

from bist_signal_bot.events.blackout import BlackoutPolicyManager
from bist_signal_bot.events.models import EventRiskDecision

def test_default_policies():
    manager = BlackoutPolicyManager()
    policies = manager.default_policies()

    assert len(policies) >= 3

    halt_policy = manager.get_policy("Trading Halt Critical")
    assert halt_policy is not None
    assert halt_policy.decision == EventRiskDecision.RESEARCH_BLOCK
