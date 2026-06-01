import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from unittest.mock import patch, MagicMock
from bist_signal_bot.cli.main import run_cli

@patch("bist_signal_bot.cli.commands.print_output")
def test_cli_divergence_detect_mock_basic(mock_print):
    # Using mock source to prevent real network calls
    args = ["divergence", "detect", "ASELS", "--source", "mock", "--level", "basic"]
    exit_code = run_cli(args)
    assert exit_code == 0
    mock_print.assert_called()

@patch("bist_signal_bot.cli.commands.print_output")
def test_cli_divergence_detect_mock_advanced(mock_print):
    args = ["divergence", "detect", "ASELS", "--source", "mock", "--level", "advanced"]
    exit_code = run_cli(args)
    assert exit_code == 0
    mock_print.assert_called()

@patch("bist_signal_bot.cli.commands.print_output")
def test_cli_divergence_detect_mock_full(mock_print):
    args = ["divergence", "detect", "ASELS", "--source", "mock", "--level", "full"]
    exit_code = run_cli(args)
    assert exit_code == 0
    mock_print.assert_called()

@patch("bist_signal_bot.cli.commands.print_output")
def test_cli_divergence_detect_mock_custom(mock_print):
    args = ["divergence", "detect", "ASELS", "--source", "mock", "--indicators", "rsi", "obv", "--pivot-mode", "CONFIRMED_LAGGED", "--confirmation-bars", "3"]
    exit_code = run_cli(args)
    assert exit_code == 0
    mock_print.assert_called()

@patch("bist_signal_bot.cli.commands.print_output")
def test_cli_divergence_detect_json(mock_print):
    args = ["divergence", "detect", "ASELS", "--source", "mock", "--level", "basic", "--json"]
    exit_code = run_cli(args)
    assert exit_code == 0
    # ensure_ascii=False in our formatting
    mock_print.assert_called()
    call_args = mock_print.call_args[0]
    # first arg should be the dictionary we dump to json
    assert "symbol" in call_args[0]
