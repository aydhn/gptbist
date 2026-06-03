import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.local_ui.fallback import LocalUIFallbackRenderer
from bist_signal_bot.local_ui.layout import LocalUILayoutBuilder

def test_fallback_renderer_plain_text():
    settings = Settings()
    layout = LocalUILayoutBuilder(settings).build_layout()
    renderer = LocalUIFallbackRenderer(settings)
    text = renderer.render_plain_text_layout(layout)
    assert "BIST Signal Bot - Operator Console" in text
    assert "PAGE: HOME" in text
    assert "Status: PASS" in text

def test_fallback_message():
    renderer = LocalUIFallbackRenderer(Settings())
    msg = renderer.fallback_message("Test reason")
    assert "[LOCAL UI FALLBACK]" in msg
    assert "Test reason" in msg
