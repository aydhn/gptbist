import pytest
from unittest.mock import patch, MagicMock
from bist_signal_bot.quality.coverage import CoverageRunner
from bist_signal_bot.quality.models import QualitySuite, QualityCheckStatus

@patch("bist_signal_bot.quality.coverage.subprocess.run")
def test_coverage_not_available(mock_run):
    mock_run.side_effect = Exception("Tool not found")
    runner = CoverageRunner()
    res = runner.run_coverage(QualitySuite.FAST, threshold_pct=60.0, timeout_seconds=10)
    assert res.status == QualityCheckStatus.SKIP
    assert "not available" in res.message

@patch("bist_signal_bot.quality.coverage.subprocess.run")
def test_coverage_below_threshold(mock_run):
    def mock_run_side_effect(*args, **kwargs):
        res = MagicMock()
        res.returncode = 0
        if "coverage" in args[0] and "--version" in args[0]:
            pass
        elif "report" in args[0]:
            res.stdout = "Name  Stmts  Miss  Cover\n-------------------------\nTOTAL    100    50    50%"
            res.stderr = ""
        else:
             pass
        return res

    mock_run.side_effect = mock_run_side_effect

    runner = CoverageRunner()
    res = runner.run_coverage(QualitySuite.FAST, threshold_pct=60.0, timeout_seconds=10)
    assert res.status in [QualityCheckStatus.FAIL, QualityCheckStatus.ERROR]
    assert "below threshold" in res.message

def test_parse_coverage_output():
    runner = CoverageRunner()
    output = "Name  Stmts  Miss  Cover\n-------------------------\nTOTAL    100    20    80%"
    summary = runner.parse_coverage_output(output, threshold_pct=70.0)
    assert summary.total_coverage_pct == 80.0
    assert summary.passed_threshold is True
