import pytest
from bist_signal_bot.cli.main import run_cli
from bist_signal_bot.stress.models import StressSeverity

def test_cli_stress_config(capsys):
    try:
        run_cli(["stress", "config"])
    except SystemExit as e:
        assert e.code == 0
    captured = capsys.readouterr()
    assert "Stress Testing Config" in captured.out
