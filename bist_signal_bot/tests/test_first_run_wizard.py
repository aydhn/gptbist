import pytest
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.deployment.first_run import FirstRunWizard
from bist_signal_bot.deployment.models import DeploymentProfileType, DeploymentStatus

def test_first_run_wizard_dry_run(tmp_path):
    settings = Settings()
    wizard = FirstRunWizard(settings, tmp_path)
    result = wizard.run(profile_type=DeploymentProfileType.RESEARCH_ONLY, confirm_write=False, dry_run=True)

    assert result.status == DeploymentStatus.PASS
    assert len(result.environment_checks) > 0
    assert len(result.steps) >= 2

def test_first_run_wizard_blocked_by_critical(tmp_path, monkeypatch):
    settings = Settings()
    settings.DEPLOYMENT_MIN_PYTHON_VERSION = "99.0" # Force fail on version

    wizard = FirstRunWizard(settings, tmp_path)
    result = wizard.run(profile_type=DeploymentProfileType.RESEARCH_ONLY, confirm_write=False, dry_run=True)

    assert result.status == DeploymentStatus.BLOCKED
    assert "Blocked by critical environment checks" in result.errors[0]
