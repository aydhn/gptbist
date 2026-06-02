import pytest
from unittest.mock import patch
from bist_signal_bot.cli.data_import_cli import handle_data_import_cmd
from argparse import Namespace

@patch("bist_signal_bot.cli.data_import_cli.LocalImportAdapterRegistry")
def test_cli_formats(mock_registry):
    mock_instance = mock_registry.return_value
    mock_instance.supported_formats.return_value = []
    args = Namespace(import_cmd="formats", json=False)
    handle_data_import_cmd(args, None)
    mock_instance.supported_formats.assert_called_once()
