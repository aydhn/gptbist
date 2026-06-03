import pytest
from pathlib import Path
from bist_signal_bot.maintenance_automation.storage import MaintenanceAutomationStore
from bist_signal_bot.maintenance_automation.models import MaintenanceCadencePolicy, MaintenanceCadenceKind
from bist_signal_bot.maintenance_automation.cadence import MaintenanceCadenceRegistry

def test_storage_save_load_policies(tmp_path):
    store = MaintenanceAutomationStore(tmp_path)
    registry = MaintenanceCadenceRegistry()
    policies = registry.default_policies()

    store.save_cadence_policies(policies)
    loaded = store.load_cadence_policies()

    assert len(loaded) == len(policies)
    assert loaded[0].cadence == policies[0].cadence

def test_storage_append_load_run(tmp_path):
    store = MaintenanceAutomationStore(tmp_path)
    from bist_signal_bot.maintenance_automation.planner import MaintenancePlanner
    from bist_signal_bot.maintenance_automation.runner import MaintenanceRunner

    planner = MaintenancePlanner()
    plan = planner.create_plan(MaintenanceCadenceKind.DAILY)
    runner = MaintenanceRunner()
    run = runner.run_plan(plan)

    store.append_run(run)

    loaded = store.load_latest_run()
    assert loaded is not None
    assert loaded.run_id == run.run_id
