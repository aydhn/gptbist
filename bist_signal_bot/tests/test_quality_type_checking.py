import pytest
from unittest.mock import patch
from bist_signal_bot.quality.type_checking import TypeCheckRunner
from bist_signal_bot.quality.models import QualityCheckStatus

@patch("bist_signal_bot.quality.type_checking.subprocess.run")
def test_mypy_not_available(mock_run):
    mock_run.side_effect = Exception("Tool not found")
    runner = TypeCheckRunner()
    res = runner.run_mypy()
    assert res.status == QualityCheckStatus.SKIP
    assert "not available" in res.message
