import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.local_ui.runner import LocalUIRunner
from bist_signal_bot.local_ui.models import LocalUIBackend, LocalUIStatus

def test_runner_launch_dry_run():
    settings = Settings(ENABLE_LOCAL_UI=True)
    runner = LocalUIRunner(settings)
    res = runner.launch(backend=LocalUIBackend.PLAIN_TEXT, dry_run=True)
    assert res.status == LocalUIStatus.PASS
    assert len(res.rendered_pages) > 0
    assert res.backend == LocalUIBackend.PLAIN_TEXT

def test_run_shortcut_dry_run():
    settings = Settings()
    runner = LocalUIRunner(settings)
    from bist_signal_bot.local_ui.shortcuts import LocalUIShortcutRegistry
    reg = LocalUIShortcutRegistry(settings)
    shortcut = reg.default_shortcuts()[0]
    res = runner.run_shortcut(shortcut, dry_run=True)
    assert res["status"] == "SUCCESS"

def test_run_unsafe_shortcut_blocked():
    settings = Settings(LOCAL_UI_BLOCK_WRITE_ACTIONS=True, LOCAL_UI_BLOCK_UNSAFE_COMMANDS=True)
    runner = LocalUIRunner(settings)
    from bist_signal_bot.local_ui.shortcuts import LocalUIShortcutRegistry
    reg = LocalUIShortcutRegistry(settings)
    shortcut = reg.blocked_shortcuts()[0]
    res = runner.run_shortcut(shortcut, dry_run=False)
    assert res["status"] == "BLOCKED"
    assert "safety check failed" in res["message"]
