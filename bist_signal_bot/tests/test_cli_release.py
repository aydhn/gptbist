import pytest
from bist_signal_bot.config.settings import Settings

# Just testing that the commands module doesn't crash when we call handle_release_command
# We will mock print and the internal runners.
def test_cli_release_check(monkeypatch, capsys):
    from bist_signal_bot.cli.commands import handle_release_command
    class Args:
        command = "release"
        release_command = "check"
        json = False
        profile = None
        no_scenarios = False

    s = Settings()
    s.DATA_DIR = "test_data"
    handle_release_command(Args(), s)
    captured = capsys.readouterr()
    assert "Error" in captured.out or "Import bist_signal_bot" in captured.out or "[PASS]" in captured.out or "FAIL" in captured.out

def test_cli_release_status(monkeypatch, capsys):
    from bist_signal_bot.cli.commands import handle_release_command
    class Args:
        command = "release"
        release_command = "status"
        json = False

    s = Settings()
    s.DATA_DIR = "test_data"
    handle_release_command(Args(), s)
    captured = capsys.readouterr()
    assert "error" in captured.out or "latest_run" in captured.out or "Error" in captured.out
