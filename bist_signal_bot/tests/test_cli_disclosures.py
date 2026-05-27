import pytest
from bist_signal_bot.cli.commands_disclosures import handle_disclosures

class MockArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_cli_disclosures_config(capsys):
    args = MockArgs(subcommand="config", json=False)
    handle_disclosures(args)
    captured = capsys.readouterr()
    assert "ENABLE_DISCLOSURE_INTELLIGENCE" in captured.out

def test_cli_disclosures_recent(capsys):
    args = MockArgs(subcommand="recent", limit=5, json=False)
    handle_disclosures(args)
    captured = capsys.readouterr()
    # It might be empty, but should not crash
    assert captured.err == ""
