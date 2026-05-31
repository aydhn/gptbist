import pytest
from bist_signal_bot.leaderboard.policy import SelectionPolicyRegistry
from bist_signal_bot.leaderboard.models import CandidateType
from bist_signal_bot.config.settings import Settings

def test_selection_policy_weights_normalize():
    settings = Settings()
    registry = SelectionPolicyRegistry(settings=settings)
    weights = {"A": 2.0, "B": 2.0}
    normalized = registry.normalize_weights(weights)
    assert normalized["A"] == 0.5
    assert normalized["B"] == 0.5

def test_selection_policy_defaults():
    settings = Settings()
    registry = SelectionPolicyRegistry(settings=settings)
    policies = registry.default_policies()
    assert len(policies) > 0
    strat_policy = registry.get_policy("strategy_research_selection_v1")
    assert strat_policy is not None
    assert strat_policy.candidate_type == CandidateType.STRATEGY

def test_selection_policy_negative_weights_warning():
    registry = SelectionPolicyRegistry(settings=Settings())
    policy = registry.get_policy("strategy_research_selection_v1")
    policy.weights["A"] = -1.0
    warnings = registry.validate_policy(policy)
    assert any("negative" in w for w in warnings)
