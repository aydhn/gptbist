import sys
from unittest.mock import patch
from bist_signal_bot.cli.commands import run_monitoring_cli

class DummyArgs:
    pass

def test_cli_monitoring_status(capsys):
    args = DummyArgs()
    args.monitoring_cmd = "status"
    args.json = False
    run_monitoring_cli(args)
    captured = capsys.readouterr()
    assert "Monitoring is operational" in captured.out
