import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.cli.research_orchestrator_cli import get_parser, main

def test_cli_parser_orchestrator():
    parser = get_parser()
    args = parser.parse_args(["plan", "--campaign", "QUICK_RESEARCH_SCAN", "--dry-run"])
    assert args.command == "plan"
    assert args.campaign == "QUICK_RESEARCH_SCAN"
    assert args.dry_run is True

def test_cli_main_campaigns_list(capsys):
    main(["campaigns"])
    captured = capsys.readouterr()
    assert "Quick Research Scan" in captured.out
