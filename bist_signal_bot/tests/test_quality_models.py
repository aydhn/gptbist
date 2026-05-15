import pytest
from bist_signal_bot.quality.models import (
    QualityCheckStatus,
    QualityGateLevel,
    QualityTool,
    QualitySuite,
    QualityCheckResult,
    TestRunSummary,
    CoverageSummary,
    StaticAnalysisSummary,
    RegressionSmokeCommand,
    QualityRunConfig,
    QualityRunResult
)

def test_quality_check_status_enum():
    assert QualityCheckStatus.PASS == "PASS"
    assert QualityCheckStatus.FAIL == "FAIL"

def test_quality_run_config_validation():
    config = QualityRunConfig()
    assert config.suite == QualitySuite.FAST
    assert config.gate_level == QualityGateLevel.STANDARD
    assert config.coverage_threshold_pct == 60.0

    # Test invalid threshold
    with pytest.raises(ValueError):
        QualityRunConfig(coverage_threshold_pct=150.0)

def test_regression_smoke_command_validation():
    cmd = RegressionSmokeCommand(name="test", command=["echo", "test"], timeout_seconds=10)
    assert cmd.name == "test"
    assert cmd.command == ["echo", "test"]

    with pytest.raises(ValueError):
         RegressionSmokeCommand(name="", command=["echo", "test"], timeout_seconds=10)

    with pytest.raises(ValueError):
         RegressionSmokeCommand(name="test", command=[], timeout_seconds=10)

    with pytest.raises(ValueError):
         RegressionSmokeCommand(name="test", command=["echo", "test"], timeout_seconds=-5)

def test_quality_check_result_summary():
    result = QualityCheckResult(
        check_name="test_check",
        tool=QualityTool.PYTEST,
        status=QualityCheckStatus.PASS,
        message="Passed",
        elapsed_seconds=1.5,
        exit_code=0
    )
    summary = result.summary()
    assert summary["check_name"] == "test_check"
    assert summary["tool"] == "PYTEST"
    assert summary["status"] == "PASS"
    assert summary["elapsed_seconds"] == 1.5

def test_quality_run_result_summary():
    config = QualityRunConfig()
    result = QualityRunResult(
        run_id="test-123",
        config=config,
        status=QualityCheckStatus.PASS,
        elapsed_seconds=5.0
    )
    summary = result.summary()
    assert summary["run_id"] == "test-123"
    assert summary["status"] == "PASS"
    assert summary["checks_total"] == 0
