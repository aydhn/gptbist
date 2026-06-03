import pytest
from bist_signal_bot.app.healthcheck import check_local_ui
from bist_signal_bot.config.settings import Settings

def test_check_local_ui_pass():
    settings = Settings()
    res = check_local_ui(settings)
    assert res["status"] == "PASS"
    assert "PLAIN_TEXT" in res["capabilities"]

def test_check_local_ui_fail(monkeypatch):
    settings = Settings()

    def mock_detect_capabilities(self):
        raise ValueError("Simulated error")

    import bist_signal_bot.local_ui.capabilities
    monkeypatch.setattr(bist_signal_bot.local_ui.capabilities.LocalUICapabilityDetector, "detect_capabilities", mock_detect_capabilities)

    res = check_local_ui(settings)
    assert res["status"] == "FAIL"
    assert "Simulated error" in res["message"]
