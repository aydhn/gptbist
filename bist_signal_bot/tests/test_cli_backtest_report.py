import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
import json
from unittest.mock import patch, MagicMock
import pandas as pd

from bist_signal_bot.cli.commands_backtest import handle_backtest_command
from bist_signal_bot.backtesting.models import BacktestResult

class MockArgs:
    def __init__(self, **kwargs):
        self.command = "backtest"
        self.backtest_cmd = "report"
        self.symbol = "ASELS"
        self.source = "mock"
        self.strategy = "moving_average_trend"
        self.report = True
        self.format = "json"
        self.report_format = "json"
        self.compare_benchmark = None
        self.compare_default_benchmarks = False
        self.output_dir = None
        self.risk_free_rate = None
        self.periods_per_year = None
        for k, v in kwargs.items():
            setattr(self, k, v)

@patch("bist_signal_bot.cli.commands.cmd_backtest_report")
def test_cmd_backtest_report_json(mock_report):
    mock_report.return_value = 0
    ctx = MagicMock()
    args = MockArgs(format="json", json=True)
    ret = handle_backtest_command(args, ctx)
    assert ret == 0
    mock_report.assert_called_once_with(args, ctx)

@patch("bist_signal_bot.cli.commands.cmd_backtest_report")
def test_cmd_backtest_report_markdown(mock_report):
    mock_report.return_value = 0
    ctx = MagicMock()
    args = MockArgs(format="markdown", report_format="markdown")
    ret = handle_backtest_command(args, ctx)
    assert ret == 0
    mock_report.assert_called_once_with(args, ctx)
