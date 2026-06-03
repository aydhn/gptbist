import pytest
from bist_signal_bot.maintenance_automation.models import MaintenanceCadencePolicy, MaintenanceCadenceKind
from bist_signal_bot.maintenance_automation.cadence import MaintenanceCadenceRegistry

def test_cadence_policy_disclaimer():
    policy = MaintenanceCadencePolicy(
        policy_id="test",
        name="Test Policy",
        cadence=MaintenanceCadenceKind.DAILY,
        actions=[],
        disclaimer="bad disclaimer"
    )
    registry = MaintenanceCadenceRegistry()
    errors = registry.validate_policy(policy)
    assert len(errors) > 0
    assert "not investment advice" in errors[0]

def test_cadence_registry_default_policies():
    registry = MaintenanceCadenceRegistry()
    policies = registry.default_policies()
    assert len(policies) > 0
    assert any(p.cadence == MaintenanceCadenceKind.WEEKLY for p in policies)

def test_cadence_registry_weekly_actions():
    registry = MaintenanceCadenceRegistry()
    weekly_policies = registry.policies_by_cadence(MaintenanceCadenceKind.WEEKLY)
    assert len(weekly_policies) > 0
    assert len(weekly_policies[0].actions) > 0
