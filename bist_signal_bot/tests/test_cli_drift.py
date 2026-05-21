import pytest
from bist_signal_bot.cli.commands import run_drift_command
from bist_signal_bot.config.settings import Settings
import argparse

class MockArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_cli_drift_snapshot(capsys):
    s = Settings()
    s.DRIFT_SAVE_RESULTS = False
    args = MockArgs(
        command="drift",
        subcommand="snapshot",
        domains=["MODEL_SCORE", "SIGNAL_OUTCOME"],
        symbols=[],
        save=False,
        json=False
    )

    run_drift_command(args, s)
    captured = capsys.readouterr()
    assert "Drift Analysis Report" in captured.out
    assert "Status" in captured.out
