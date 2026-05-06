import pytest
from unittest.mock import patch, MagicMock
from bist_signal_bot.cli.commands import handle_portfolio_risk_command
import argparse
from bist_signal_bot.app.bootstrap import ApplicationContext
from bist_signal_bot.config.settings import Settings

@patch("bist_signal_bot.cli.commands.run_portfolio_risk_evaluate")
def test_cli_portfolio_evaluate(mock_run):
    args = argparse.Namespace(portfolio_command="evaluate")
    ctx = MagicMock()
    ctx.settings = Settings()
    ctx.logger = MagicMock()
    handle_portfolio_risk_command(args, ctx)
    mock_run.assert_called_once()
