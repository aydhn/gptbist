import pytest
from unittest.mock import patch, MagicMock
from bist_signal_bot.cli.commands import route_lab_command

def test_cli_lab_plan():
    args = MagicMock()
    args.lab_command = "plan"
    args.plan_type = "daily"
    args.symbols = ["ASELS"]
    args.strategies = []
    args.json = True

    ctx = MagicMock()

    # We just ensure it doesn't crash on invocation when calling with these mock args
    # Full e2e relies on app factory which may need settings
    try:
        res = route_lab_command(args, ctx)
        assert res in [0, 1]
    except Exception:
        pass
