import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
import argparse
from bist_signal_bot.cli.parsers import add_execution_sim_parser

def test_cli_execution_sim_cost_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_execution_sim_parser(subparsers)

    args = parser.parse_args(["execution-sim", "cost", "--symbol", "ASELS", "--side", "BUY", "--price", "100", "--quantity", "100", "--json"])
    assert args.command == "execution-sim"
    assert args.exec_cmd == "cost"
    assert args.symbol == "ASELS"
    assert args.json is True
