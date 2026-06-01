import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.app.healthcheck import _append_security_health
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_security():
    settings = Settings()

    status_dict = {}
    _append_security_health(status_dict, settings)

    assert "security" in status_dict
    assert status_dict["security"]["enabled"] == settings.ENABLE_SECURITY_GUARD
    assert status_dict["security"]["secret_redactor_capable"] is True
