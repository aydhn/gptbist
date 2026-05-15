import pytest
from unittest.mock import MagicMock
from bist_signal_bot.quality.gate import QualityGateRunner
from bist_signal_bot.quality.models import (
    QualityCheckResult, QualityCheckStatus, QualityRunConfig, QualityTool,
    QualityGateLevel, QualityTool
)

def test_gate_eval_relaxed():
    runner = QualityGateRunner()
    config = QualityRunConfig(gate_level=QualityGateLevel.RELAXED)
    checks = [
        QualityCheckResult(check_name="test1", tool=QualityTool.MYPY, status=QualityCheckStatus.SKIP, message="skipped")
    ]
    status = runner.evaluate_gate(checks, config)
    assert status == QualityCheckStatus.PASS

def test_gate_eval_standard_fail():
    runner = QualityGateRunner()
    config = QualityRunConfig(gate_level=QualityGateLevel.STANDARD)
    checks = [
        QualityCheckResult(check_name="test1", tool=QualityTool.PYTEST, status=QualityCheckStatus.FAIL, message="failed")
    ]
    status = runner.evaluate_gate(checks, config)
    assert status == QualityCheckStatus.FAIL

def test_gate_eval_warning_fail_on_warning():
    runner = QualityGateRunner()
    config = QualityRunConfig(gate_level=QualityGateLevel.STANDARD, fail_on_warning=True)
    checks = [
        QualityCheckResult(check_name="test1", tool=QualityTool.RUFF, status=QualityCheckStatus.WARN, message="warn")
    ]
    status = runner.evaluate_gate(checks, config)
    assert status == QualityCheckStatus.FAIL

def test_gate_eval_release_missing_tools():
    runner = QualityGateRunner()
    # Missing regression, security, import, coverage
    config = QualityRunConfig(gate_level=QualityGateLevel.RELEASE, run_coverage=True, run_security_checks=True, run_regression_smoke=True, run_import_checks=True)
    checks = [
        QualityCheckResult(check_name="test1", tool=QualityTool.PYTEST, status=QualityCheckStatus.PASS, message="passed")
    ]
    status = runner.evaluate_gate(checks, config)
    assert status == QualityCheckStatus.FAIL
