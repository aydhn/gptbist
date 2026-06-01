import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import argparse
from bist_signal_bot.cli.parsers import build_parser
from bist_signal_bot.cli.commands import handle_review_workflow

def test_cli_rw_create(capsys):
    parser = build_parser()
    args = parser.parse_args(["review-workflow", "create", "--symbol", "ASELS"])
    handle_review_workflow(args)
    captured = capsys.readouterr()
    assert "Created case" in captured.out
    assert "ASELS" in captured.out

def test_cli_rw_journal_add_note(capsys):
    parser = build_parser()
    args = parser.parse_args(["review-workflow", "journal", "c1", "--add-note", "test"])
    handle_review_workflow(args)
    captured = capsys.readouterr()
    assert "Added note to c1: test" in captured.out

def test_cli_rw_signoff_request(capsys):
    parser = build_parser()
    args = parser.parse_args(["review-workflow", "signoff", "c1", "--request", "--reason", "Test"])
    handle_review_workflow(args)
    captured = capsys.readouterr()
    assert "Requested signoff for c1" in captured.out
