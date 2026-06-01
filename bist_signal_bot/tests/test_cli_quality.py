import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
import sys
import argparse
from unittest.mock import patch, MagicMock

from bist_signal_bot.cli.commands import handle_quality_command
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.quality.models import QualityRunResult, QualityRunConfig, QualityCheckStatus

class MockArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

@patch("bist_signal_bot.app.quality_app.QualityGateRunner")
def test_cli_quality_run(mock_create_runner):
    mock_runner = MagicMock()
    config = QualityRunConfig()
    real_res = QualityRunResult(run_id="123", config=config, status=QualityCheckStatus.PASS, elapsed_seconds=1.5)
    mock_runner.run.return_value = real_res
    mock_create_runner.return_value = mock_runner

    settings = Settings()
    args = MockArgs(quality_command="run", suite="FAST", gate="STANDARD", json=False)

    # Should not exit
    handle_quality_command(args, settings)

    mock_runner.run.assert_called_once()

@patch("bist_signal_bot.app.quality_app.QualityGateRunner")
def test_cli_quality_run_fail(mock_create_runner):
    mock_runner = MagicMock()
    config = QualityRunConfig()
    real_res = QualityRunResult(run_id="123", config=config, status=QualityCheckStatus.FAIL, elapsed_seconds=1.5)
    mock_runner.run.return_value = real_res
    mock_create_runner.return_value = mock_runner

    settings = Settings()
    args = MockArgs(quality_command="run", suite="FAST", gate="STANDARD", json=False)

    # Should exit 1
    with pytest.raises(SystemExit) as e:
        handle_quality_command(args, settings)
    assert e.value.code == 1

@patch("bist_signal_bot.app.quality_app.QualityGateRunner")
def test_cli_quality_smoke(mock_create_runner):
    mock_runner = MagicMock()
    config = QualityRunConfig()
    real_res = QualityRunResult(run_id="123", config=config, status=QualityCheckStatus.PASS, elapsed_seconds=1.5)
    mock_runner.run.return_value = real_res
    mock_create_runner.return_value = mock_runner

    settings = Settings()
    args = MockArgs(quality_command="smoke", json=False)

    handle_quality_command(args, settings)
    mock_runner.run.assert_called_once()

@patch("bist_signal_bot.app.quality_app.QualityGateRunner")
def test_cli_quality_config(mock_create_runner):
    mock_runner = MagicMock()
    mock_create_runner.return_value = mock_runner

    settings = Settings()
    args = MockArgs(quality_command="config", json=False)

    # Just checking it doesn't crash
    handle_quality_command(args, settings)
