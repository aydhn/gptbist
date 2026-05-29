import pytest

def test_cli_context_build_help():
    # Given we use argparse, we just verify the module loads without syntax error
    from bist_signal_bot.cli.context_commands import setup_context_parser
    assert callable(setup_context_parser)
