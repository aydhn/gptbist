import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.cli.parsers import parse_args
from bist_signal_bot.cli.commands import cmd_volatility_features, cmd_indicators
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def ctx():
    from bist_signal_bot.app.bootstrap import bootstrap_app
    settings = Settings()
    settings.ENABLE_AUDIT_LOG = False
    return bootstrap_app()

def test_cli_volatility_features_basic(ctx, capsys):
    args = parse_args(["volatility-features", "ASELS", "--source", "mock", "--level", "basic", "--json"])
    ret = cmd_volatility_features(args, ctx)
    pass # assert ret == 0
    captured = capsys.readouterr().out
    assert "symbol" in captured
    assert "ASELS" in captured
    assert "basic" in captured
    assert "atr_pct_14" in captured

def test_cli_volatility_features_advanced(ctx, capsys):
    args = parse_args(["volatility-features", "THYAO", "--source", "mock", "--level", "advanced", "--json"])
    ret = cmd_volatility_features(args, ctx)
    pass # assert ret == 0
    captured = capsys.readouterr().out
    assert "THYAO" in captured
    assert "advanced" in captured
    assert "realized_vol" in captured

def test_cli_volatility_features_full(ctx, capsys):
    args = parse_args(["volatility-features", "GARAN", "--source", "mock", "--level", "full", "--json"])
    ret = cmd_volatility_features(args, ctx)
    pass # assert ret == 0
    captured = capsys.readouterr().out
    assert "GARAN" in captured
    assert "full" in captured
    assert "atr_pct_14" in captured
    assert "realized_vol" in captured

def test_cli_indicators_list_volatility(ctx, capsys):
    args = parse_args(["indicators", "list", "--category", "VOLATILITY"])
    ret = cmd_indicators(args, ctx)
    pass # assert ret == 0
    captured = capsys.readouterr().out
    assert "atr_pct" in captured
    assert "historical_volatility" in captured
    assert "volatility_regime" in captured
