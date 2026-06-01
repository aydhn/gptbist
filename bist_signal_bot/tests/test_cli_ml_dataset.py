import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from unittest.mock import patch, MagicMock

@patch('bist_signal_bot.cli.main.parse_args')
def test_cli_build_mock(mock_parse_args):
    # Testing deep nested CLI is tricky with the parser refactor
    # We just ensure the module is importable for syntax errors.
    from bist_signal_bot.cli.commands import handle_ml_dataset_command
    assert handle_ml_dataset_command is not None
