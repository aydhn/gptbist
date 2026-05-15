import pytest
import sys
import platform
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.packaging.environment import EnvironmentDoctor
from bist_signal_bot.packaging.models import PlatformType, EnvironmentCheckStatus

def test_detect_platform():
    doc = EnvironmentDoctor(Settings())
    plat = doc.detect_platform()
    assert plat in [PlatformType.WINDOWS, PlatformType.LINUX, PlatformType.MACOS, PlatformType.UNKNOWN]

def test_check_python_version():
    doc = EnvironmentDoctor(Settings(PACKAGING_MIN_PYTHON_VERSION="3.0.0"))
    res = doc.check_python_version()
    assert res.status == EnvironmentCheckStatus.PASS

def test_check_project_root(tmp_path):
    # Should warn if no project files exist
    doc = EnvironmentDoctor(Settings(), base_dir=tmp_path)
    res = doc.check_project_root()
    assert res.status == EnvironmentCheckStatus.WARN

    # Should pass if pyproject.toml exists
    (tmp_path / "pyproject.toml").touch()
    res = doc.check_project_root()
    assert res.status == EnvironmentCheckStatus.PASS

def test_check_write_permissions(tmp_path):
    doc = EnvironmentDoctor(Settings(PACKAGING_CHECK_WRITE_PERMISSIONS=True))
    test_dir = tmp_path / "test_write"
    res = doc.check_write_permissions([test_dir])
    assert res.status == EnvironmentCheckStatus.PASS
    assert test_dir.exists()

def test_run_doctor(tmp_path):
    settings = Settings(PACKAGING_CHECK_WRITE_PERMISSIONS=False)
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "bist_signal_bot").mkdir()
    (tmp_path / "bist_signal_bot" / "__main__.py").touch()
    (tmp_path / ".env.example").touch()

    doc = EnvironmentDoctor(settings, base_dir=tmp_path)
    report = doc.run_doctor(include_dependencies=False)

    assert report.overall_status in [EnvironmentCheckStatus.PASS, EnvironmentCheckStatus.WARN]
    assert len(report.checks) >= 5
