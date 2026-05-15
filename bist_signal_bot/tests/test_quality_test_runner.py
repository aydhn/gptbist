import pytest
from unittest.mock import patch, MagicMock
from bist_signal_bot.quality.test_runner import QualityTestRunner
from bist_signal_bot.quality.models import QualitySuite, QualityCheckStatus

def test_run_command_success():
    runner = QualityTestRunner()
    exit_code, stdout, stderr, elapsed = runner.run_command(["echo", "hello"], timeout_seconds=2)
    assert exit_code == 0
    assert "hello" in stdout

def test_run_command_timeout():
    runner = QualityTestRunner()
    # Using python -c 'import time; time.sleep(2)' to simulate timeout
    exit_code, stdout, stderr, elapsed = runner.run_command(["python", "-c", "import time; time.sleep(2)"], timeout_seconds=1)
    assert exit_code == -1
    assert "Timeout after 1s" in stderr

def test_parse_pytest_summary():
    runner = QualityTestRunner()
    output = "=== 3 passed, 1 failed, 2 warnings in 0.12s ==="
    summary = runner.parse_pytest_summary(output, elapsed_seconds=0.12)
    assert summary.passed == 3
    assert summary.failed == 1
    assert summary.duration_seconds == 0.12

@patch("bist_signal_bot.quality.test_runner.subprocess.run")
def test_run_pytest_success(mock_run):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "=== 5 passed in 0.1s ==="
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    runner = QualityTestRunner()
    res = runner.run_pytest(QualitySuite.FAST, timeout_seconds=10)
    assert res.status == QualityCheckStatus.PASS
    assert res.exit_code == 0

@patch("bist_signal_bot.quality.test_runner.subprocess.run")
def test_run_pytest_failure(mock_run):
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "=== 1 failed in 0.1s ==="
    mock_result.stderr = ""
    mock_run.return_value = mock_result

    runner = QualityTestRunner()
    res = runner.run_pytest(QualitySuite.UNIT, timeout_seconds=10)
    assert res.status == QualityCheckStatus.FAIL
    assert res.exit_code == 1
