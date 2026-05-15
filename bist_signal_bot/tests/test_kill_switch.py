import pytest
from bist_signal_bot.security.kill_switch import KillSwitchManager
from bist_signal_bot.security.models import KillSwitchScope
from bist_signal_bot.config.settings import Settings

def test_kill_switch_activate_saves_state(tmp_path):
    settings = Settings()
    manager = KillSwitchManager(settings, base_dir=tmp_path)

    manager.activate([KillSwitchScope.RUNTIME], "Emergency stop")
    state = manager.load_state()

    assert state.enabled is True
    assert KillSwitchScope.RUNTIME in state.scopes
    assert state.reason == "Emergency stop"

def test_kill_switch_deactivate_requires_confirm(tmp_path):
    settings = Settings()
    manager = KillSwitchManager(settings, base_dir=tmp_path)
    manager.activate([KillSwitchScope.ALL], "test")

    with pytest.raises(ValueError):
        manager.deactivate()

def test_kill_switch_deactivate_with_confirm_clears_state(tmp_path):
    settings = Settings()
    manager = KillSwitchManager(settings, base_dir=tmp_path)
    manager.activate([KillSwitchScope.ALL], "test")

    manager.deactivate(confirm=True)
    state = manager.load_state()

    assert state.enabled is False
