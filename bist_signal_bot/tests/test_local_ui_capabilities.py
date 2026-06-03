import pytest
from bist_signal_bot.local_ui.capabilities import LocalUICapabilityDetector
from bist_signal_bot.local_ui.models import LocalUIBackend

class MockSettings:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __getattr__(self, name):
        return None

def test_detect_plain_text_always_available():
    detector = LocalUICapabilityDetector(MockSettings(LOCAL_UI_ALLOW_RICH=False, LOCAL_UI_ALLOW_TEXTUAL=False, LOCAL_UI_ALLOW_CURSES=False))
    caps = detector.detect_capabilities()
    plain = next((c for c in caps if c.backend == LocalUIBackend.PLAIN_TEXT), None)
    assert plain is not None
    assert plain.available is True

def test_preferred_backend_fallback():
    settings = MockSettings(
        ENABLE_LOCAL_UI=True,
        LOCAL_UI_BACKEND="AUTO",
        LOCAL_UI_FALLBACK_TO_PLAIN_TEXT=True,
        LOCAL_UI_ALLOW_RICH=False,
        LOCAL_UI_ALLOW_TEXTUAL=False,
        LOCAL_UI_ALLOW_CURSES=False
    )
    detector = LocalUICapabilityDetector(settings)
    pref = detector.preferred_backend()
    assert pref == LocalUIBackend.PLAIN_TEXT

def test_missing_rich_fallback(monkeypatch):
    settings = MockSettings(ENABLE_LOCAL_UI=True, LOCAL_UI_BACKEND="AUTO")
    detector = LocalUICapabilityDetector(settings)

    def mock_dependency_available(name):
        return False, None

    monkeypatch.setattr(detector, "dependency_available", mock_dependency_available)
    pref = detector.preferred_backend()
    assert pref == LocalUIBackend.PLAIN_TEXT

def test_detect_backend():
    settings = MockSettings(ENABLE_LOCAL_UI=True, LOCAL_UI_ALLOW_RICH=False, LOCAL_UI_ALLOW_TEXTUAL=False, LOCAL_UI_ALLOW_CURSES=False)
    detector = LocalUICapabilityDetector(settings)
    cap = detector.detect_backend(LocalUIBackend.PLAIN_TEXT)
    assert cap.available is True
