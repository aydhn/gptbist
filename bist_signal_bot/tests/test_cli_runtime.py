import pytest
from bist_signal_bot.cli.commands import cmd_runtime
from bist_signal_bot.config.settings import Settings

class MockArgs:
    def __init__(self, **kwargs):
        self.runtime_command = 'run-once'
        self.source = 'mock'
        self.strategy = 'moving_average_trend'
        self.group = None
        self.symbols = None
        self.ml_filter = False
        self.ml_model_id = None
        self.regime_filter = False
        self.paper = False
        self.telegram = False
        self.json = False
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_cli_runtime_run_once(capsys):
    settings = Settings()
    args = MockArgs(runtime_command='dry-run')
    cmd_runtime(args, settings)

    captured = capsys.readouterr()
    assert "Status: SUCCESS" in captured.out or "Status:" in captured.out

def test_cli_runtime_status(capsys):
    settings = Settings()
    args = MockArgs(runtime_command='status')
    cmd_runtime(args, settings)

    captured = capsys.readouterr()
    assert "Runtime Status" in captured.out

def test_cli_runtime_unlock(capsys):
    settings = Settings()
    args = MockArgs(runtime_command='unlock', stale_only=True)
    cmd_runtime(args, settings)

    captured = capsys.readouterr()
    assert "lock" in captured.out.lower()

def test_cli_runtime_config(capsys):
    settings = Settings()
    args = MockArgs(runtime_command='config', json=True)
    cmd_runtime(args, settings)

    captured = capsys.readouterr()
    assert "{" in captured.out