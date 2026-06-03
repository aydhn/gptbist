import pytest
from bist_signal_bot.maintenance_automation.models import RetentionPolicy, MaintenanceArtifactKind
from bist_signal_bot.maintenance_automation.retention import RetentionPolicyRegistry

def test_retention_registry_defaults():
    registry = RetentionPolicyRegistry()
    policies = registry.default_retention_policies()
    assert len(policies) > 0
    assert any(p.artifact_kind == MaintenanceArtifactKind.CACHE for p in policies)

def test_retention_registry_invalid_days():
    policy = RetentionPolicy(
        retention_id="test",
        artifact_kind=MaintenanceArtifactKind.CUSTOM,
        path_pattern="**/*",
        retention_days=-1
    )
    registry = RetentionPolicyRegistry()
    errors = registry.validate_retention_policy(policy)
    assert len(errors) > 0
