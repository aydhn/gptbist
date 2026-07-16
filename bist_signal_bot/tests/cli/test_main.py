import pytest
from bist_signal_bot.cli.main import run_cli
import sys

def test_run_cli_explain(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["bist_signal_bot", "explain", "--help"])
    try:
        run_cli(["explain", "--help"])
    except SystemExit:
        pass
