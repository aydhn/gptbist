import json
from unittest.mock import patch, MagicMock

from bist_signal_bot.cli.commands import cmd_corporate_actions, cmd_adjust_data
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.app.bootstrap import ApplicationContext

class MockArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_corporate_actions_init(tmp_path):
    settings = Settings(CORPORATE_ACTIONS_DIR_NAME=str(tmp_path.name), CORPORATE_ACTIONS_FILE_NAME="actions.json")
    # Patch the get_corporate_actions_dir to use tmp_path
    with patch("bist_signal_bot.data.corporate_actions.get_corporate_actions_dir", return_value=tmp_path), \
         patch("bist_signal_bot.data.corporate_actions.get_corporate_actions_file_path", return_value=tmp_path / "actions.json"):


        ctx = MagicMock(spec=ApplicationContext)
        ctx.settings = settings
        ctx.audit_logger = MagicMock()
        args = MockArgs(ca_command="init", overwrite=True, json=True)

        with patch('bist_signal_bot.cli.formatting.print_output') as mock_print:
            res = cmd_corporate_actions(args, ctx)
            assert res == 0
            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            assert "Initialized" in output["message"]
            assert (tmp_path / "actions.json").exists()

def test_corporate_actions_list(tmp_path):
    settings = Settings(CORPORATE_ACTIONS_DIR_NAME=str(tmp_path.name), CORPORATE_ACTIONS_FILE_NAME="actions.json")

    with patch("bist_signal_bot.data.corporate_actions.get_corporate_actions_dir", return_value=tmp_path), \
         patch("bist_signal_bot.data.corporate_actions.get_corporate_actions_file_path", return_value=tmp_path / "actions.json"):

        ctx = MagicMock()
        ctx.settings = settings

        # Init first
        args_init = MockArgs(ca_command="init", overwrite=True, json=True)
        cmd_corporate_actions(args_init, ctx)

        # Add one
        args_add = MockArgs(ca_command="add", symbol="ASELS", date="2025-07-01", type="SPLIT", ratio=2.0, cash=None, description="Test", json=True)
        cmd_corporate_actions(args_add, ctx)

        # List
        args_list = MockArgs(ca_command="list", symbol=None, json=True)
        with patch('bist_signal_bot.cli.formatting.print_output') as mock_print:
            res = cmd_corporate_actions(args_list, ctx)
            assert res == 0
            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            assert isinstance(output, list)
            assert len(output) == 1
            assert output[0]["symbol"] == "ASELS"
            assert output[0]["action_type"] == "SPLIT"
