import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.local_ui.shortcuts import LocalUIShortcutRegistry
from bist_signal_bot.local_ui.models import LocalUIPageKind

def test_default_safe_shortcuts():
    registry = LocalUIShortcutRegistry(Settings())
    shortcuts = registry.default_shortcuts()
    assert len(shortcuts) > 0
    assert any("healthcheck" in s.command for s in shortcuts)

def test_blocked_shortcut_detection():
    settings = Settings(LOCAL_UI_BLOCK_ORDER_TERMS=True, LOCAL_UI_BLOCK_BROKER_TERMS=True)
    registry = LocalUIShortcutRegistry(settings)

    blocked = registry.blocked_shortcuts()[0]
    errors = registry.validate_shortcut(blocked)
    assert errors
    assert any("blocked term" in e for e in errors)

def test_shortcuts_for_page():
    registry = LocalUIShortcutRegistry(Settings())
    shortcuts = registry.shortcuts_for_page(LocalUIPageKind.HEALTHCHECK)
    assert len(shortcuts) == 1
    assert shortcuts[0].shortcut_id == "healthcheck_all"

def test_safe_shortcut_summary():
    registry = LocalUIShortcutRegistry(Settings())
    shortcuts = registry.default_shortcuts()
    summary = registry.safe_shortcut_summary(shortcuts[0])
    assert "shortcut_id" in summary
    assert "dry_run" in summary
