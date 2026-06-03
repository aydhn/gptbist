import pytest
from bist_signal_bot.maintenance_automation.models import MaintenanceCadenceKind, MaintenanceStatus, MaintenanceAction, MaintenanceActionType
from bist_signal_bot.maintenance_automation.planner import MaintenancePlanner
from bist_signal_bot.maintenance_automation.runner import MaintenanceRunner

def test_runner_dry_run():
    planner = MaintenancePlanner()
    plan = planner.create_plan(MaintenanceCadenceKind.DAILY, dry_run=True)
    runner = MaintenanceRunner()
    run = runner.run_plan(plan)
    assert run.status == MaintenanceStatus.PASS
    for res in run.results:
        assert res.dry_run is True

def test_runner_unsafe_command_skipped():
    action = MaintenanceAction(
        action_id="test_unsafe",
        action_type=MaintenanceActionType.CUSTOM,
        name="Test Unsafe",
        command="broker execute order"
    )
    runner = MaintenanceRunner()
    res = runner.run_action(action, dry_run=True)
    assert res.status == MaintenanceStatus.BLOCKED
    assert res.skipped is True

def test_runner_cleanup_confirm():
    action = MaintenanceAction(
        action_id="test_destructive",
        action_type=MaintenanceActionType.CACHE_CLEANUP,
        name="Destructive",
        destructive=True,
        requires_confirm=True
    )
    runner = MaintenanceRunner()
    res = runner.run_action(action, dry_run=True, confirm=False)
    assert res.status == MaintenanceStatus.SKIPPED
    assert res.skipped is True
