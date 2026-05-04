import pytest
from unittest.mock import patch, MagicMock
from bist_signal_bot.cli.main import run_cli

@patch("bist_signal_bot.cli.commands_backtest.print")
def test_cli_backtest_run_mock(mock_print):
    argv = ["backtest", "run", "ASELS", "--strategy", "moving_average_trend", "--source", "mock", "--initial-capital", "1000"]
    ret = run_cli(argv)
    assert ret == 0
    mock_print.assert_called()

@patch("bist_signal_bot.cli.formatting.print_output")
def test_cli_backtest_run_json(mock_print_output):
    argv = ["backtest", "run", "ASELS", "--strategy", "moving_average_trend", "--source", "mock", "--json"]
    ret = run_cli(argv)
    assert ret == 0
    mock_print_output.assert_called()
    args, kwargs = mock_print_output.call_args


@patch("bist_signal_bot.cli.commands_backtest.print")
def test_cli_backtest_batch_mock(mock_print):
    argv = ["backtest", "batch", "--strategy", "moving_average_trend", "--symbols", "ASELS", "THYAO", "--source", "mock"]
    ret = run_cli(argv)
    assert ret == 0
    mock_print.assert_called()
