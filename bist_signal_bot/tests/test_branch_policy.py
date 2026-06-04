import pytest
from bist_signal_bot.release_policy.models import BranchPolicy, BranchKind, ChangeType

def test_branch_policy_disclaimer():
    bp = BranchPolicy(
        policy_id="test",
        branch_kind=BranchKind.MAIN,
        name_pattern="^main$",
        allowed_change_types=[],
        requires_qa=True,
        requires_ops=True,
        requires_final_audit=True,
        requires_changelog=True,
        requires_migration_notes=True,
        requires_compatibility_check=True,
        protected=True
    )
    assert "investment advice" in bp.disclaimer

def test_version_snapshot_validation():
    from bist_signal_bot.release_policy.versioning import VersionGovernanceEngine
    from bist_signal_bot.release_policy.models import VersionSnapshot

    engine = VersionGovernanceEngine()
    snap = VersionSnapshot(
        snapshot_id="1",
        project_version="1.0.0",
        schema_version="invalid",
        config_version="1.0.0",
        cli_contract_version="1.0.0",
        data_contract_version="1.0.0"
    )
    errors = engine.validate_version_snapshot(snap)
    assert len(errors) > 0
    assert any("invalid" in e for e in errors)

def test_branch_policy_registry():
    from bist_signal_bot.release_policy.branch_policy import BranchPolicyRegistry

    registry = BranchPolicyRegistry()
    policies = registry.default_branch_policies()
    assert len(policies) > 0

    main_policy = registry.policy_for_branch("main")
    assert main_policy is not None
    assert main_policy.protected is True

    release_policy = registry.policy_for_branch("release/1.0.0")
    assert release_policy is not None
    assert release_policy.requires_qa is True

    exp_policy = registry.policy_for_branch("experimental/foo")
    assert exp_policy is not None
    assert any("release artifacts" in w for w in exp_policy.warnings)
