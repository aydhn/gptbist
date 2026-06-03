import pytest
from bist_signal_bot.maintenance_automation.models import MaintenanceCadenceKind, MaintenanceAction, MaintenanceActionType
from bist_signal_bot.maintenance_automation.planner import MaintenancePlanner

def test_planner_default_dry_run():
    planner = MaintenancePlanner()
    plan = planner.create_plan(MaintenanceCadenceKind.DAILY)
    assert plan.dry_run is True
    assert plan.confirm is False

def test_planner_estimate_destructive():
    planner = MaintenancePlanner()
    plan = planner.create_plan(MaintenanceCadenceKind.MONTHLY)
    assert plan.estimated_destructive_actions > 0

def test_planner_destructive_blocked_without_confirm():
    planner = MaintenancePlanner()
    plan = planner.create_plan(MaintenanceCadenceKind.MONTHLY, confirm=False)
    # The status should be WATCH because it contains destructive actions and confirm is False
    assert plan.status.value == "WATCH"
    assert any("skipped" in w.lower() for w in plan.warnings)
