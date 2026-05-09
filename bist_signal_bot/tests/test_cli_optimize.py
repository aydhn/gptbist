import pytest
from bist_signal_bot.cli.parsers import parse_args
from bist_signal_bot.cli.commands import cmd_optimize
from bist_signal_bot.app.bootstrap import bootstrap_app

def test_cli_optimize_search_space():
    args = parse_args(["optimize", "search-space", "--strategy", "moving_average_trend", "--json"])
    assert args.command == "optimize"
    assert args.opt_command == "search-space"

def test_cli_optimize_strategy_parse():
    args = parse_args(["optimize", "strategy", "ASELS", "--source", "mock", "--strategy", "moving_average_trend", "--method", "GRID_SEARCH"])
    assert args.command == "optimize"
    assert args.opt_command == "strategy"
    assert args.symbol == "ASELS"
    assert args.method == "GRID_SEARCH"

def test_cli_optimize_walk_forward_parse():
    args = parse_args(["optimize", "walk-forward", "ASELS", "--source", "mock", "--strategy", "moving_average_trend", "--train-window", "100"])
    assert args.command == "optimize"
    assert args.opt_command == "walk-forward"
    assert args.train_window == 100

def test_cli_optimize_recent_parse():
    args = parse_args(["optimize", "recent", "--limit", "10"])
    assert args.opt_command == "recent"
    assert args.limit == 10
