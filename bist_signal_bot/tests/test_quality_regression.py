import pytest
from bist_signal_bot.quality.regression import RegressionSmokeRunner
from bist_signal_bot.quality.models import RegressionSmokeCommand

def test_default_commands():
    runner = RegressionSmokeRunner()
    cmds = runner.default_commands()
    assert len(cmds) > 0
    names = [c.name for c in cmds]
    assert "cli_help" in names
    assert "healthcheck" in names

def test_smoke_commands_timeout():
    runner = RegressionSmokeRunner()
    cmd = RegressionSmokeCommand(name="sleep_test", command=["python", "-c", "import time; time.sleep(2)"], timeout_seconds=1)
    res = runner.run_smoke_commands([cmd])
    assert len(res) == 1
    assert res[0].status.value == "ERROR"
    assert "timed out" in res[0].message
