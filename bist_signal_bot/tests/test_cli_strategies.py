import pytest
import sys
from io import StringIO
from bist_signal_bot.cli.main import run_cli

def test_cli_strategies_list(monkeypatch):
    captured_out = StringIO()
    monkeypatch.setattr(sys, 'stdout', captured_out)

    # Argparse expects the command as the first argument, not the script name
    res = run_cli(["strategies", "list"])
    assert res == 0
    assert "Registered Strategies" in captured_out.getvalue()
