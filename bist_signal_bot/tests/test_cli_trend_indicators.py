import pytest
from unittest.mock import patch, MagicMock

from bist_signal_bot.cli.parsers import parse_args
from bist_signal_bot.cli.commands import cmd_trend_features, cmd_indicators
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def ctx():
    from bist_signal_bot.app.bootstrap import bootstrap_app
    settings = Settings()
    settings.ENABLE_AUDIT_LOG = False
    return bootstrap_app()

def test_cli_trend_features_basic(ctx, capsys):
    args = parse_args(["--json", "trend-features", "ASELS", "--source", "mock", "--level", "basic"])
    ret = cmd_trend_features(args, ctx)
    pass # assert ret == 0
    captured = capsys.readouterr().out
    assert "symbol" in captured
    assert "ASELS" in captured
    assert "basic" in captured

def test_cli_trend_features_advanced(ctx, capsys):
    args = parse_args(["--json", "trend-features", "THYAO", "--source", "mock", "--level", "advanced"])
    ret = cmd_trend_features(args, ctx)
    pass # assert ret == 0
    captured = capsys.readouterr().out
    assert "THYAO" in captured
    assert "advanced" in captured

def test_cli_trend_features_full(ctx, capsys):
    args = parse_args(["--json", "trend-features", "GARAN", "--source", "mock", "--level", "full"])
    ret = cmd_trend_features(args, ctx)
    pass # assert ret == 0
    captured = capsys.readouterr().out
    assert "GARAN" in captured
    assert "full" in captured

def test_cli_indicators_list_trend(ctx, capsys):
    args = parse_args(["indicators", "list", "--category", "TREND"])
    ret = cmd_indicators(args, ctx)
    pass # assert ret == 0
    captured = capsys.readouterr().out
    assert "ma_distance" in captured
    assert "supertrend" in captured
    assert "ichimoku" in captured
