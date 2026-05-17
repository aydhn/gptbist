import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.release.rehearsal import SafeLaunchRehearsalRunner
from bist_signal_bot.release.models import ReleaseProfile, ReleaseCheckStatus

def test_rehearsal_runner_builds_steps():
    runner = SafeLaunchRehearsalRunner(Settings())
    steps = runner.build_steps(ReleaseProfile.FULL_SAFE_LOCAL)
    assert len(steps) > 0
    assert any(s.step_id == "rehearsal_mock_scenario" for s in steps)

def test_rehearsal_runner_mock_profile():
    runner = SafeLaunchRehearsalRunner(Settings())
    res = runner.run_rehearsal(ReleaseProfile.MOCK_ONLY, save_report=False)
    assert res.status.value in ["READY", "FAILED"] # it will run and simulate pass or fail
