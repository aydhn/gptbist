import sys
from bist_signal_bot.cli.commands import handle_feature_store_command
class MockArgs:
    feature_store_command = "contracts"
    show_contract = None
    json = True

def test_cli_feature_store_contracts(capsys):
    args = MockArgs()
    from bist_signal_bot.config.settings import Settings
    handle_feature_store_command(args, Settings())
    out, _ = capsys.readouterr()
    assert "ok" in out
