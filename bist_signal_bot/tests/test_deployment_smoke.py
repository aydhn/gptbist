import pytest
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.deployment.smoke import DeploymentSmokeTester
from bist_signal_bot.deployment.models import DeploymentProfileType, DeploymentStatus, EnvironmentCheckResult, EnvironmentCheckType
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

import subprocess
import uuid
from bist_signal_bot.deployment.models import DeploymentDecision

def test_deployment_smoke_tester_run_command_failed(tmp_path, monkeypatch):
    settings = Settings()
    tester = DeploymentSmokeTester(settings, str(tmp_path))

    def mock_run(*args, **kwargs):
        class MockProcess:
            returncode = 1
            stderr = "mock error"
        return MockProcess()

    monkeypatch.setattr(subprocess, "run", mock_run)
    res = tester.run_command(["failing_command"])
    assert res.status == DeploymentStatus.FAIL
    assert res.decision == DeploymentDecision.BLOCK
    assert "failed with code 1" in res.message

def test_deployment_smoke_tester_run_command_timeout(tmp_path, monkeypatch):
    settings = Settings()
    tester = DeploymentSmokeTester(settings, str(tmp_path))

    def mock_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="mock", timeout=30)

    monkeypatch.setattr(subprocess, "run", mock_run)
    res = tester.run_command(["timeout_command"])
    assert res.status == DeploymentStatus.FAIL
    assert res.decision == DeploymentDecision.BLOCK
    assert "timed out" in res.message

def test_deployment_smoke_tester_run_command_exception(tmp_path, monkeypatch):
    settings = Settings()
    tester = DeploymentSmokeTester(settings, str(tmp_path))

    def mock_run(*args, **kwargs):
        raise Exception("mock generic error")

    monkeypatch.setattr(subprocess, "run", mock_run)
    res = tester.run_command(["error_command"])
    assert res.status == DeploymentStatus.FAIL
    assert res.decision == DeploymentDecision.BLOCK
    assert "Error executing command" in res.message

def test_deployment_smoke_tester_not_dry_run(tmp_path, monkeypatch):
    settings = Settings()
    tester = DeploymentSmokeTester(settings, str(tmp_path))
    profile = DeploymentProfileManager().get_profile(DeploymentProfileType.RESEARCH_ONLY)

    def mock_run_command(*args, **kwargs):
        return EnvironmentCheckResult(
            check_id=str(uuid.uuid4()),
            check_type=EnvironmentCheckType.CUSTOM,
            status=DeploymentStatus.FAIL,
            decision=DeploymentDecision.BLOCK,
            title="Smoke Command Failed",
            message="Command failed"
        )

    monkeypatch.setattr(tester, "run_command", mock_run_command)
    result = tester.run_smoke_tests(profile, dry_run=False)

    assert result.status == DeploymentStatus.FAIL
    assert len(result.checks) > 0
    assert all(c.status == DeploymentStatus.FAIL for c in result.checks)
