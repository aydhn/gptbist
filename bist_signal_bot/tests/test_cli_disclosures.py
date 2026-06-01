import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.cli.parsers import build_parser
def test_cli_parser_disclosures():
    parser = build_parser()
    args = parser.parse_args(["disclosures", "import", "--file", "test.csv"])
    assert args.command == "disclosures"
    assert args.disc_command == "import"
    assert args.file == "test.csv"
