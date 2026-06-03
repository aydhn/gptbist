import pytest
from pathlib import Path
from bist_signal_bot.maintenance_automation.models import (
    MaintenanceAction, MaintenanceActionType, MaintenanceCadencePolicy,
    MaintenanceCadenceKind, RetentionPolicy, MaintenanceArtifactKind
)
from bist_signal_bot.maintenance_automation.cadence import MaintenanceCadenceRegistry
from bist_signal_bot.maintenance_automation.planner import MaintenancePlanner
from bist_signal_bot.maintenance_automation.runner import MaintenanceRunner
from bist_signal_bot.maintenance_automation.cleanup import MaintenanceCleanupEngine
from bist_signal_bot.maintenance_automation.retention import RetentionPolicyRegistry
from bist_signal_bot.maintenance_automation.backup import BackupManifestBuilder
from bist_signal_bot.maintenance_automation.manifest import MaintenanceManifestBuilder
from bist_signal_bot.maintenance_automation.staleness import MaintenanceStalenessDetector
from bist_signal_bot.core.exceptions import MaintenanceAutomationError

def test_destructive_requires_confirm():
    with pytest.raises(ValueError):
        MaintenanceAction(action_id="1", action_type=MaintenanceActionType.CACHE_CLEANUP, name="x", destructive=True, requires_confirm=False)

def test_unsafe_broker_command_blocked():
    action = MaintenanceAction(action_id="1", action_type=MaintenanceActionType.CUSTOM, name="x", command="broker sell AAPL")
    assert any("BLOCKED" in w for w in action.warnings)

def test_cadence_policy_disclaimer():
    pol = MaintenanceCadencePolicy(policy_id="p1", name="n", cadence=MaintenanceCadenceKind.DAILY, actions=[])
    assert "not investment advice" in pol.disclaimer
    assert "No real order" in pol.disclaimer

def test_cadence_registry_defaults():
    reg = MaintenanceCadenceRegistry()
    assert len(reg.default_policies()) > 0
    weekly = reg.policies_by_cadence(MaintenanceCadenceKind.WEEKLY)
    assert len(weekly) > 0

def test_planner_dry_run():
    planner = MaintenancePlanner()
    pol = MaintenanceCadencePolicy(policy_id="p1", name="n", cadence=MaintenanceCadenceKind.DAILY, actions=[])
    plan = planner.plan_from_policy(pol)
    assert plan.dry_run is True

def test_planner_estimates_destructive_and_skips():
    action = MaintenanceAction(action_id="1", action_type=MaintenanceActionType.CACHE_CLEANUP, name="x", destructive=True, requires_confirm=True)
    pol = MaintenanceCadencePolicy(policy_id="p1", name="n", cadence=MaintenanceCadenceKind.DAILY, actions=[action])
    plan = MaintenancePlanner().plan_from_policy(pol, dry_run=False, confirm=False)
    assert plan.estimated_destructive_actions == 1
    assert plan.status == "WATCH"

def test_runner_skips_destructive_without_confirm():
    action = MaintenanceAction(action_id="1", action_type=MaintenanceActionType.CACHE_CLEANUP, name="x", destructive=True, requires_confirm=True)
    pol = MaintenanceCadencePolicy(policy_id="p1", name="n", cadence=MaintenanceCadenceKind.DAILY, actions=[action])
    plan = MaintenancePlanner().plan_from_policy(pol, confirm=False)
    run = MaintenanceRunner().run_plan(plan)
    assert run.results[0].skipped is True
    assert run.results[0].status == "SKIPPED"

def test_cleanup_engine_safe_to_delete():
    engine = MaintenanceCleanupEngine()
    assert engine.safe_to_delete(Path("script.py"), MaintenanceArtifactKind.CACHE) is False
    assert engine.safe_to_delete(Path("docs/README.md"), MaintenanceArtifactKind.CACHE) is False
    assert engine.safe_to_delete(Path("data/cache/tmp123.bin"), MaintenanceArtifactKind.CACHE) is True

def test_cleanup_engine_dry_run():
    engine = MaintenanceCleanupEngine()
    from bist_signal_bot.maintenance_automation.models import CleanupCandidate
    c = CleanupCandidate(candidate_id="1", artifact_kind=MaintenanceArtifactKind.CACHE, path="tmp.bin", reason="stale")
    res = engine.cleanup(c, dry_run=True, confirm=False)
    assert res["status"] == "SKIPPED"

def test_retention_policy_invalid_days():
    reg = RetentionPolicyRegistry()
    pol = RetentionPolicy(retention_id="1", artifact_kind=MaintenanceArtifactKind.CACHE, path_pattern="*", retention_days=-5)
    errs = reg.validate_retention_policy(pol)
    assert len(errs) > 0

def test_backup_manifest_builder():
    builder = BackupManifestBuilder()
    manifest = builder.build_backup_manifest([Path("data")], dry_run=True)
    assert len(manifest.checksum_manifest) > 0
    assert "not investment advice" in manifest.disclaimer

def test_staleness_detector():
    det = MaintenanceStalenessDetector()
    assert isinstance(det.detect_failed_recent_jobs(), list)

def test_manifest_builder_no_real_order():
    mb = MaintenanceManifestBuilder()
    pol = MaintenanceCadencePolicy(policy_id="p1", name="n", cadence=MaintenanceCadenceKind.DAILY, actions=[])
    plan = MaintenancePlanner().plan_from_policy(pol)
    run = MaintenanceRunner().run_plan(plan)
    man = mb.build_run_manifest(run)
    assert man.no_real_order_sent is True
