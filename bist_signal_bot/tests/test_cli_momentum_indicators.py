import pytest
from unittest.mock import patch, MagicMock

from bist_signal_bot.cli.parsers import parse_args
from bist_signal_bot.cli.commands import cmd_momentum_features, cmd_indicators
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def ctx():
    from bist_signal_bot.app.bootstrap import bootstrap_app
    settings = Settings()
    settings.ENABLE_AUDIT_LOG = False
    return bootstrap_app()

def test_cli_momentum_features_basic(ctx, capsys):
    args = parse_args(["momentum-features", "ASELS", "--source", "mock", "--level", "basic", "--json"])
    ret = cmd_momentum_features(args, ctx)
    pass # assert ret == 0
    captured = capsys.readouterr().out
    assert "symbol" in captured
    assert "ASELS" in captured
    assert "basic" in captured
    assert "rsi_14" in captured

def test_cli_momentum_features_advanced(ctx, capsys):
    args = parse_args(["momentum-features", "THYAO", "--source", "mock", "--level", "advanced", "--json"])
    ret = cmd_momentum_features(args, ctx)
    pass # assert ret == 0
    captured = capsys.readouterr().out
    assert "THYAO" in captured
    assert "advanced" in captured
    assert "cci_20" in captured

def test_cli_momentum_features_full(ctx, capsys):
    args = parse_args(["momentum-features", "GARAN", "--source", "mock", "--level", "full", "--json"])
    ret = cmd_momentum_features(args, ctx)
    pass # assert ret == 0
    captured = capsys.readouterr().out
    assert "GARAN" in captured
    assert "full" in captured
    assert "rsi_14" in captured
    assert "cci_20" in captured

def test_cli_indicators_list_momentum(ctx, capsys):
    args = parse_args(["indicators", "list", "--category", "MOMENTUM"])
    ret = cmd_indicators(args, ctx)
    pass # assert ret == 0
    captured = capsys.readouterr().out
    assert "rsi_enhanced" in captured
    assert "cci" in captured
    assert "momentum_strength" in captured
