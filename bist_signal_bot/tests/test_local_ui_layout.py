import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.local_ui.layout import LocalUILayoutBuilder
from bist_signal_bot.local_ui.models import LocalUIBackend

def test_layout_builder_default_pages():
    builder = LocalUILayoutBuilder(Settings())
    pages = builder.default_pages()
    assert len(pages) >= 10
    assert any(p.page_id == "HOME" for p in pages)
    assert any(p.page_id == "HEALTHCHECK" for p in pages)

def test_layout_builder_navigation_order():
    builder = LocalUILayoutBuilder(Settings())
    layout = builder.build_layout(backend=LocalUIBackend.PLAIN_TEXT)
    assert len(layout.navigation_order) == len(layout.pages)
    assert layout.navigation_order[0] == "HOME"

def test_layout_validation():
    builder = LocalUILayoutBuilder(Settings())
    layout = builder.build_layout(backend=LocalUIBackend.PLAIN_TEXT)
    errors = builder.validate_layout(layout)
    assert not errors

def test_layout_summary():
    builder = LocalUILayoutBuilder(Settings())
    layout = builder.build_layout(backend=LocalUIBackend.PLAIN_TEXT)
    summary = builder.layout_summary(layout)
    assert summary["page_count"] > 0
    assert summary["status"] == "PASS"
