import pytest
from unittest.mock import patch, MagicMock
from bist_signal_bot.quality.static_analysis import StaticAnalysisRunner
from bist_signal_bot.quality.models import QualityCheckStatus

@patch("bist_signal_bot.quality.static_analysis.subprocess.run")
def test_static_tool_not_available(mock_run):
    mock_run.side_effect = Exception("Tool not found")
    runner = StaticAnalysisRunner()
    res = runner.run_ruff()
    assert res.status == QualityCheckStatus.SKIP
    assert "not available" in res.message
