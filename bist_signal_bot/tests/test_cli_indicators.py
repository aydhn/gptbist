import pytest
from unittest.mock import patch, MagicMock
from bist_signal_bot.cli.main import run_cli
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def mock_app_context():
    with patch("bist_signal_bot.cli.main.bootstrap_app") as mock_bootstrap:
        ctx = MagicMock()
        ctx.settings = Settings()
        mock_bootstrap.return_value = ctx
        yield ctx

def test_cli_indicators_list(mock_app_context, capsys):
    res = run_cli(["indicators", "list"])
    assert res == 0
    captured = capsys.readouterr()
    assert "Registered Indicators" in captured.out
    assert "sma" in captured.out

def test_cli_indicators_list_json(mock_app_context, capsys):
    res = run_cli(["indicators", "list", "--json"])
    assert res == 0
    captured = capsys.readouterr()
    assert "{" in captured.out

def test_cli_indicators_calc_mock(mock_app_context, capsys):
    res = run_cli(["indicators", "calc", "ASELS", "--source", "mock", "--indicator", "sma:window=20"])
    assert res == 0
    captured = capsys.readouterr()
    assert "Indicator Calculation Result for ASELS" in captured.out
    assert "Success: 1" in captured.out
    assert "sma_20" in captured.out

def test_cli_indicators_calc_default_set(mock_app_context, capsys):
    res = run_cli(["indicators", "calc", "ASELS", "--source", "mock", "--default-set"])
    assert res == 0
    captured = capsys.readouterr()
    assert "Success: 10" in captured.out

def test_cli_indicators_calc_json(mock_app_context, capsys):
    res = run_cli(["indicators", "calc", "ASELS", "--source", "mock", "--indicator", "sma:window=20", "--json"])
    assert res == 0
    captured = capsys.readouterr()
    assert "{" in captured.out
