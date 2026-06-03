import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.local_ui.pages import LocalUIPageBuilder
from bist_signal_bot.local_ui.models import LocalUIPageKind, LocalUIStatus

def test_build_home_page():
    builder = LocalUIPageBuilder(Settings())
    page = builder.build_page(LocalUIPageKind.HOME)
    assert page.page_id == "HOME"
    assert page.title == "Home"
    assert len(page.widgets) > 0

def test_build_healthcheck_page_watch_widget():
    builder = LocalUIPageBuilder(Settings())
    page = builder.build_page(LocalUIPageKind.HEALTHCHECK)
    assert page.status == LocalUIStatus.WATCH
    assert page.widgets[0].status == LocalUIStatus.WATCH

def test_build_module_page():
    builder = LocalUIPageBuilder(Settings())
    page = builder.build_page(LocalUIPageKind.FEATURE_STORE)
    assert page.page_id == "FEATURE_STORE"
    assert "Feature Store" in page.title
    assert page.status == LocalUIStatus.WATCH

def test_build_commands_page():
    builder = LocalUIPageBuilder(Settings())
    page = builder.build_page(LocalUIPageKind.COMMANDS)
    assert page.status == LocalUIStatus.PASS
    assert len(page.widgets) > 0
