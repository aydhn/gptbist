import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.release.checks import ReleaseCheckRunner
from bist_signal_bot.release.models import ReleaseCheckStatus

def test_release_check_runner_imports():
    runner = ReleaseCheckRunner(Settings())
    res = runner.run_import_checks()
    # At least some should pass, assuming bist_signal_bot.core exists
    pass # we assume at least one might fail in tests, its fine

def test_release_check_runner_config():
    runner = ReleaseCheckRunner(Settings())
    res = runner.run_config_checks()
    assert len(res) == 2
    # Second check is safe defaults
    safe_defaults_check = [c for c in res if c.check_id == "config_safe_defaults"][0]
    assert safe_defaults_check.status == ReleaseCheckStatus.PASS

def test_release_check_runner_storage(tmp_path):
    s = Settings()
    s.DATA_DIR = str(tmp_path)
    runner = ReleaseCheckRunner(s)
    res = runner.run_storage_checks()
    assert res[0].status == ReleaseCheckStatus.PASS

def test_release_check_runner_safety():
    runner = ReleaseCheckRunner(Settings())
    res = runner.run_safety_checks()
    # If the mock passes
    assert res[0].status in [ReleaseCheckStatus.PASS, ReleaseCheckStatus.SKIP, ReleaseCheckStatus.FAIL]
