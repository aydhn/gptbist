import pytest
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.deployment.doctor import EnvironmentDoctor
from bist_signal_bot.deployment.models import DeploymentStatus

def test_environment_doctor_python_version(tmp_path):
    settings = Settings()
    # Assume tests are run on supported python version
    doctor = EnvironmentDoctor(settings, tmp_path)
    res = doctor.check_python_version()
    assert res.status == DeploymentStatus.PASS

def test_environment_doctor_filesystem_tmp_path(tmp_path):
    settings = Settings()
    doctor = EnvironmentDoctor(settings, tmp_path)
    res = doctor.check_filesystem()
    assert res.status == DeploymentStatus.PASS

def test_environment_doctor_disk_space_low(tmp_path, monkeypatch):
    settings = Settings()
    settings.DEPLOYMENT_DOCTOR_MIN_FREE_DISK_MB = 999999999 # Impractically high
    doctor = EnvironmentDoctor(settings, tmp_path)
    res = doctor.check_disk_space()
    assert res.status in [DeploymentStatus.WARN, DeploymentStatus.FAIL]

def test_environment_doctor_secret_hygiene(tmp_path):
    settings = Settings()
    doctor = EnvironmentDoctor(settings, tmp_path)
    res = doctor.check_secret_hygiene()
    assert res.status == DeploymentStatus.PASS
