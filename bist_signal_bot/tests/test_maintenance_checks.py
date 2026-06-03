import pytest
from bist_signal_bot.maintenance_automation.models import MaintenanceStatus
from bist_signal_bot.maintenance_automation.checks import MaintenanceCheckRunner

def test_check_runner_healthcheck():
    runner = MaintenanceCheckRunner()
    res = runner.run_healthcheck_check()
    assert res.status == MaintenanceStatus.PASS
    assert "Mocked" in res.message

def test_check_runner_missing_subsystem():
    runner = MaintenanceCheckRunner()
    res = runner.run_explainability_check()
    assert res.status == MaintenanceStatus.WATCH
