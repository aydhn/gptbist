import pytest
import sys
import json
from unittest.mock import patch, MagicMock
import pandas as pd
import datetime
from pathlib import Path

from bist_signal_bot.cli.parsers import build_parser
from bist_signal_bot.cli.commands import handle_risk_commands
from bist_signal_bot.config.settings import Settings

class DummyCtx:
    def __init__(self):
        self.settings = Settings()
        self.logger = MagicMock()
        self.strategy_engine = MagicMock()

        # Mock strategy engine to return a dummy strategy
        dummy_strat = MagicMock()
        from bist_signal_bot.signals.models import SignalCandidate, SignalDirection
        dummy_signal = SignalCandidate(
            symbol="ASELS",
            strategy_name="moving_average_trend",
            direction=SignalDirection.LONG,
            score=85.0,
            confidence=90.0,
            generated_at=datetime.datetime.now(datetime.timezone.utc),
            feature_snapshot={"close": 102.0}
        )
        dummy_strat.generate.return_value = dummy_signal
        self.strategy_engine.get_strategy.return_value = dummy_strat

def test_cli_risk_evaluate(capsys):
    parser = build_parser()
    args = parser.parse_args(["risk", "evaluate", "ASELS", "--source", "mock", "--strategy", "moving_average_trend"])
    ctx = DummyCtx()

    ret = handle_risk_commands(args, ctx)
    assert ret == 0
    out, err = capsys.readouterr()
    assert "Risk Decision for ASELS" in out
    assert "moving_average_trend" in out

def test_cli_risk_evaluate_json(capsys):
    parser = build_parser()
    args = parser.parse_args(["risk", "evaluate", "ASELS", "--source", "mock", "--strategy", "moving_average_trend", "--json"])
    ctx = DummyCtx()

    ret = handle_risk_commands(args, ctx)
    assert ret == 0
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data["symbol"] == "ASELS"
    assert "status" in data

def test_cli_risk_size(capsys):
    parser = build_parser()
    args = parser.parse_args(["risk", "size", "ASELS", "--side", "LONG", "--entry", "50", "--stop", "47", "--equity", "100000"])
    ctx = DummyCtx()

    ret = handle_risk_commands(args, ctx)
    assert ret == 0
    out, err = capsys.readouterr()
    assert "Position Size Result for ASELS" in out
    assert "Entry Price: 50" in out

def test_cli_risk_size_json(capsys):
    parser = build_parser()
    args = parser.parse_args(["risk", "size", "ASELS", "--side", "LONG", "--entry", "50", "--stop", "47", "--equity", "100000", "--json"])
    ctx = DummyCtx()

    ret = handle_risk_commands(args, ctx)
    assert ret == 0
    out, err = capsys.readouterr()
    data = json.loads(out)
    assert data["symbol"] == "ASELS"
    assert data["entry_price"] == 50.0
    assert data["quantity"] > 0

def test_cli_risk_stop_target(capsys):
    parser = build_parser()
    args = parser.parse_args(["risk", "stop-target", "ASELS", "--side", "LONG", "--entry", "50", "--method-stop", "FIXED_PERCENT", "--method-target", "RISK_REWARD_MULTIPLE"])
    ctx = DummyCtx()

    ret = handle_risk_commands(args, ctx)
    assert ret == 0
    out, err = capsys.readouterr()
    assert "Stop/Target Reference for ASELS" in out
    assert "Entry: 50" in out

def test_cli_risk_config(capsys):
    parser = build_parser()
    args = parser.parse_args(["risk", "config"])
    ctx = DummyCtx()

    ret = handle_risk_commands(args, ctx)
    assert ret == 0
    out, err = capsys.readouterr()
    assert "Risk Engine Configuration" in out
    assert "ENABLE_RISK_ENGINE: True" in out
