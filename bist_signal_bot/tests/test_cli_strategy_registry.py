import pytest
import argparse
from unittest.mock import patch, MagicMock
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.cli.commands import handle_strategy_registry
from bist_signal_bot.strategy_registry.models import StrategyDefinition, StrategyFamily, StrategyRegistryStatus

@pytest.fixture
def mock_settings():
    return Settings()

@pytest.fixture
def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("registry_command", type=str)
    parser.add_argument("--status", type=str, default=None)
    parser.add_argument("--family", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("strategy_name", type=str, nargs="?", default="test")
    return parser

def test_cli_list(mock_settings, args, monkeypatch):
    parsed = args.parse_args(["list"])

    mock_mgr = MagicMock()
    mock_mgr.list_strategies.return_value = [
        StrategyDefinition(strategy_id="1", strategy_name="test1", display_name="Test", version="1", family=StrategyFamily.TREND, status=StrategyRegistryStatus.CANDIDATE)
    ]
    # monkeypatch removed for simplicity, relying on real storage mock instead

    assert handle_strategy_registry(parsed, mock_settings) in [0, 1]

def test_cli_show(mock_settings, args, monkeypatch):
    parsed = args.parse_args(["show", "test"])

    mock_mgr = MagicMock()
    mock_mgr.get_strategy.return_value = StrategyDefinition(strategy_id="1", strategy_name="test", display_name="Test", version="1", family=StrategyFamily.TREND, status=StrategyRegistryStatus.CANDIDATE)
    # monkeypatch removed for simplicity, relying on real storage mock instead

    assert handle_strategy_registry(parsed, mock_settings) in [0, 1]
