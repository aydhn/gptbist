import pytest
import json
from unittest.mock import patch, MagicMock

from bist_signal_bot.cli.commands import cmd_volume_features
from bist_signal_bot.config.settings import Settings

class MockCtx:
    def __init__(self):
        self.settings = Settings()
        self.logger = MagicMock()
        self.audit_logger = MagicMock()

class MockArgs:
    def __init__(self, symbol="ASELS", source="mock", timeframe="1d", rows=250, level="basic", save_output=False, json_out=False):
        self.symbol = symbol
        self.source = source
        self.timeframe = timeframe
        self.rows = rows
        self.level = level
        self.save_output = save_output
        self.json = json_out

def test_cmd_volume_features_mock_basic(capsys):
    args = MockArgs(level="basic")
    ctx = MockCtx()

    ret = cmd_volume_features(args, ctx)
    assert ret == 0

    captured = capsys.readouterr()
    assert "Volume Feature Calculation for ASELS" in captured.out
    assert "Level: basic" in captured.out
    assert "Volume feature summary:" in captured.out

def test_cmd_volume_features_mock_full_json(capsys):
    args = MockArgs(level="full", json_out=True)
    ctx = MockCtx()

    ret = cmd_volume_features(args, ctx)
    assert ret == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert "requested_count" in output
    assert output["requested_count"] > 0
    assert "results" in output
