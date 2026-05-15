import pytest
from datetime import datetime
from bist_signal_bot.packaging.models import (
    PlatformType, PythonEnvironmentType, DependencyStatus, EnvironmentCheckStatus,
    DependencyCheckResult, EnvironmentCheckResult, EnvironmentDoctorReport
)

def test_dependency_check_result_summary():
    res = DependencyCheckResult("pytest", "7.0", "7.4", DependencyStatus.INSTALLED, False, "OK")
    assert res.package_name == "pytest"
    assert res.status == DependencyStatus.INSTALLED

def test_environment_check_result_summary():
    res = EnvironmentCheckResult("test_check", EnvironmentCheckStatus.PASS, "Message", recommendations=["Rec 1"])
    summary = res.summary()
    assert summary["check_name"] == "test_check"
    assert summary["status"] == "PASS"
    assert summary["message"] == "Message"
    assert summary["recommendations"] == ["Rec 1"]

def test_environment_doctor_report_summary():
    res1 = EnvironmentCheckResult("check1", EnvironmentCheckStatus.PASS, "Msg1")
    report = EnvironmentDoctorReport(
        platform=PlatformType.LINUX,
        python_version="3.11.0",
        python_executable="/usr/bin/python",
        environment_type=PythonEnvironmentType.VENV,
        project_root="/app",
        checks=[res1],
        dependency_results=[],
        overall_status=EnvironmentCheckStatus.PASS,
        warnings=["A warning"]
    )
    summary = report.summary()
    assert summary["platform"] == "LINUX"
    assert summary["environment_type"] == "VENV"
    assert summary["overall_status"] == "PASS"
    assert len(summary["checks_summary"]) == 1
    assert "disclaimer" in summary
