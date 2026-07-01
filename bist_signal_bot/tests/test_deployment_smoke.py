import pytest
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.deployment.smoke import DeploymentSmokeTester
from bist_signal_bot.deployment.models import DeploymentProfileType, DeploymentStatus
from bist_signal_bot.deployment.profiles import DeploymentProfileManager

def test_deployment_smoke_tester_dry_run(tmp_path):
    settings = Settings()
    tester = DeploymentSmokeTester(settings, str(tmp_path))
    profile = DeploymentProfileManager().get_profile(DeploymentProfileType.RESEARCH_ONLY)

    result = tester.run_smoke_tests(profile, dry_run=True)
    assert result.status == DeploymentStatus.PASS
    assert len(result.checks) > 0
    assert all(c.status == DeploymentStatus.SKIPPED for c in result.checks)

def test_deployment_smoke_tester_run_command_mocked(tmp_path, monkeypatch):
    settings = Settings()
    tester = DeploymentSmokeTester(settings, str(tmp_path))

    # Simple echo command for test, avoiding actual module execution
    res = tester.run_command(["echo", "hello"])
    assert res.status == DeploymentStatus.PASS

def test_deployment_smoke_tester_run_command_blocked(tmp_path):
    settings = Settings()
    tester = DeploymentSmokeTester(settings, str(tmp_path))
    res = tester.run_command(["ls", "-la"])
    assert res.status == DeploymentStatus.FAIL
    assert "Security violation" in res.message
