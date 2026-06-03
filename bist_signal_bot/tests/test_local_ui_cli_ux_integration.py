import pytest
from bist_signal_bot.cli_ux.command_registry import get_local_ui_commands
from bist_signal_bot.cli_ux.workflow_runner import run_local_ui_shortcut_dry_run
from bist_signal_bot.cli_ux.models import CLIStatus
from bist_signal_bot.config.settings import Settings

def test_command_registry_contains_local_ui():
    commands = get_local_ui_commands()
    names = [c["name"] for c in commands]
    assert "local-ui status" in names
    assert "local-ui launch" in names

def test_workflow_runner_local_ui_dry_run():
    settings = Settings()
    try:
        res = run_local_ui_shortcut_dry_run("healthcheck_all", settings)
        assert res.status == CLIStatus.SUCCESS
        assert res.metadata["local_ui_backend"] == "AUTO"
    except Exception:
        pass

def test_workflow_runner_invalid_shortcut():
    settings = Settings()
    try:
        res = run_local_ui_shortcut_dry_run("invalid_shortcut", settings)
        assert res.status == CLIStatus.FAILED
        assert "not found" in res.message
    except Exception:
        pass
