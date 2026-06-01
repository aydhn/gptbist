import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from unittest.mock import patch, MagicMock
from bist_signal_bot.cli.parsers import parse_args
from bist_signal_bot.cli.main import run_cli
from bist_signal_bot.config.settings import Settings

@patch('bist_signal_bot.cli.main.bootstrap_app')
def test_cli_security_audit(mock_bootstrap):
    mock_app_context = MagicMock()
    mock_bootstrap.return_value = mock_app_context
    mock_app_context.settings = Settings()

    with patch('sys.stdout'):
        assert run_cli(["security", "audit", "--json"]) == 0

@patch('bist_signal_bot.cli.main.bootstrap_app')
def test_cli_security_kill_switch_status(mock_bootstrap):
    mock_app_context = MagicMock()
    mock_bootstrap.return_value = mock_app_context
    mock_app_context.settings = Settings()

    with patch('sys.stdout'):
        assert run_cli(["security", "kill-switch", "status"]) == 0

@patch('bist_signal_bot.cli.main.bootstrap_app')
def test_cli_security_redact(mock_bootstrap):
    mock_app_context = MagicMock()
    mock_bootstrap.return_value = mock_app_context
    mock_app_context.settings = Settings()

    with patch('sys.stdout'):
        assert run_cli(["security", "redact", "--text", "bot_token=123", "--json"]) == 0

@patch('bist_signal_bot.cli.main.bootstrap_app')
def test_cli_security_config(mock_bootstrap):
    mock_app_context = MagicMock()
    mock_bootstrap.return_value = mock_app_context
    mock_app_context.settings = Settings()

    with patch('sys.stdout'):
        assert run_cli(["security", "config", "--json"]) == 0
