import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
import argparse
from bist_signal_bot.cli.commands import handle_performance_command
from bist_signal_bot.config.settings import Settings

class DummyArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_cli_perf_config(capsys):
    args = DummyArgs(perf_command="config", json=False)
    settings = Settings(ENABLE_PERFORMANCE_PROFILING=True)
    handle_performance_command(args, settings)
    captured = capsys.readouterr()
    assert "ENABLE_PERFORMANCE_PROFILING" in captured.out

def test_cli_perf_resources_json(capsys):
    args = DummyArgs(perf_command="resources", json=True)
    settings = Settings(ENABLE_PERFORMANCE_PROFILING=True)
    handle_performance_command(args, settings)
    captured = capsys.readouterr()
    assert "snapshot_id" in captured.out
