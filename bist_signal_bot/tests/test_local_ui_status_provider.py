import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.local_ui.status_provider import LocalUIStatusProvider

def test_status_provider_home():
    provider = LocalUIStatusProvider(Settings())
    status = provider.collect_home_status()
    assert status["mode"] == "RESEARCH"
    assert status["overall_status"] == "PASS"

def test_status_provider_healthcheck():
    provider = LocalUIStatusProvider(Settings())
    status = provider.collect_healthcheck_status()
    assert status["status"] == "WATCH"

def test_status_provider_command_registry():
    provider = LocalUIStatusProvider(Settings())
    registry = provider.collect_command_registry()
    assert len(registry) > 0
