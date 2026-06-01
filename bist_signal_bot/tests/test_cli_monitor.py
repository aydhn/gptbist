import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
import sys
from bist_signal_bot.cli.parsers import parse_args

def parse_arguments(args):
    original_argv = sys.argv
    sys.argv = ["bist_signal_bot"] + args
    try:
        parsed = parse_args()
        return parsed
    finally:
        sys.argv = original_argv

def test_cli_monitor_status():
    args = parse_arguments(["monitor", "status"])
    assert args.command == "monitor"
    assert args.monitor_command == "status"
    assert args.json is False

def test_cli_monitor_heartbeat():
    args = parse_arguments(["monitor", "heartbeat", "--component", "RUNTIME", "--status", "HEALTHY", "--message", "test", "--json"])
    assert args.command == "monitor"
    assert args.monitor_command == "heartbeat"
    assert args.component == "RUNTIME"
    assert args.status == "HEALTHY"
    assert args.message == "test"
    assert args.json is True

def test_cli_monitor_diagnostics():
    args = parse_arguments(["monitor", "diagnostics", "--save-report"])
    assert args.monitor_command == "diagnostics"
    assert args.save_report is True

def test_cli_monitor_repair():
    args = parse_arguments(["monitor", "repair", "--dry-run"])
    assert args.monitor_command == "repair"
    assert args.dry_run is True

def test_cli_monitor_cleanup():
    args = parse_arguments(["monitor", "cleanup", "--retention-days", "10", "--confirm"])
    assert args.monitor_command == "cleanup"
    assert args.retention_days == 10
    assert args.confirm is True
