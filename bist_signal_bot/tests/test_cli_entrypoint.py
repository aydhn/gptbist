import pytest
from unittest.mock import patch, MagicMock
from bist_signal_bot.cli.main import run_cli

@patch("bist_signal_bot.cli.main.bootstrap_app")
@patch("bist_signal_bot.cli.main.cmd_version")
def test_run_cli_version(mock_cmd_version, mock_bootstrap):
    mock_cmd_version.return_value = 0
    mock_app_context = MagicMock()
    mock_bootstrap.return_value = mock_app_context
    assert run_cli(["version"]) == 0
    mock_cmd_version.assert_called_once()

@patch("bist_signal_bot.cli.main.bootstrap_app")
@patch("bist_signal_bot.cli.main.cmd_healthcheck")
def test_run_cli_default(mock_cmd_healthcheck, mock_bootstrap):
    mock_cmd_healthcheck.return_value = 0
    mock_app_context = MagicMock()
    mock_bootstrap.return_value = mock_app_context
    assert run_cli([]) == 0
    mock_cmd_healthcheck.assert_called_once()

def test_invalid_command():
    with pytest.raises(SystemExit):
        run_cli(["invalid-command"])
