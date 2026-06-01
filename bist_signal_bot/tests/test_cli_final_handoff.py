import pytest
from unittest.mock import patch, MagicMock
from bist_signal_bot.cli.commands import handle_final_handoff_command
from bist_signal_bot.config.settings import Settings

class MockArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.handoff_command = kwargs.get("handoff_command")
        self.json = kwargs.get("json", False)
        self.save = kwargs.get("save", False)
        self.audience = kwargs.get("audience", None)
        self.cadence = kwargs.get("cadence", None)
        self.latest = kwargs.get("latest", False)

def test_cli_final_handoff_build():
    args = MockArgs(handoff_command="build", save=False, json=True)
    settings = Settings(ENABLE_FINAL_HANDOFF=True)
    with patch("bist_signal_bot.cli.formatting.print_output") as mock_print:
        res = handle_final_handoff_command(args, settings)
        assert res == 0
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "handoff_id" in call_args

def test_cli_final_handoff_release_pack():
    args = MockArgs(handoff_command="release-pack", save=False, json=True)
    settings = Settings(ENABLE_FINAL_HANDOFF=True)
    with patch("bist_signal_bot.cli.formatting.print_output") as mock_print:
        res = handle_final_handoff_command(args, settings)
        assert res == 0
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "pack_id" in call_args

def test_cli_final_handoff_disabled():
    args = MockArgs(handoff_command="build", save=False, json=True)
    settings = Settings(ENABLE_FINAL_HANDOFF=False)
    with patch("bist_signal_bot.cli.formatting.print_output") as mock_print:
        res = handle_final_handoff_command(args, settings)
        assert res == 1
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "error" in call_args
