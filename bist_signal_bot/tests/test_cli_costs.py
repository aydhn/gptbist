import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import json
import pytest
from unittest.mock import patch, MagicMock

from bist_signal_bot.cli.commands import handle_costs_command
from bist_signal_bot.config.settings import Settings

class DummyArgs:
    pass

@pytest.fixture
def settings():
    return Settings(
        ENABLE_COST_MODEL=True,
        COST_SCENARIO="BASE",
    )

def test_costs_estimate_cli_json(settings, capsys):
    args = DummyArgs()
    args.costs_command = "estimate"
    args.symbol = "ASELS"
    args.side = "BUY"
    args.quantity = 100.0
    args.price = 50.0
    args.avg_daily_volume = None
    args.avg_daily_turnover = None
    args.volatility = None
    args.scenario = None
    args.json = True

    handle_costs_command(args, settings)

    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["symbol"] == "ASELS"
    assert res["side"] == "BUY"
    assert res["gross_notional"] == 5000.0

def test_costs_round_trip_cli_text(settings, capsys):
    args = DummyArgs()
    args.costs_command = "round-trip"
    args.symbol = "ASELS"
    args.side = "BUY"
    args.quantity = 100.0
    args.entry_price = 50.0
    args.exit_price = 55.0
    args.scenario = None
    args.json = False

    handle_costs_command(args, settings)

    captured = capsys.readouterr()
    assert "BIST Bot Round-Trip Maliyet Tahmini" in captured.out
    assert "ASELS" in captured.out

def test_costs_scenarios_cli(settings, capsys):
    args = DummyArgs()
    args.costs_command = "scenarios"
    args.json = False

    handle_costs_command(args, settings)
    captured = capsys.readouterr()
    assert "- OPTIMISTIC:" in captured.out

def test_costs_config_cli_json(settings, capsys):
    args = DummyArgs()
    args.costs_command = "config"
    args.json = True

    handle_costs_command(args, settings)
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert "COMMISSION_BPS" in res
    assert res["COMMISSION_BPS"] == 5.0
