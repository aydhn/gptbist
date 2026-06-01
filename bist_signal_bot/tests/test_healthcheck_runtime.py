import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.app.healthcheck import get_runtime_health
from bist_signal_bot.config.settings import Settings

def test_get_runtime_health():
    settings = Settings()
    health = get_runtime_health(settings)
    assert health["runtime_enabled"] is True
    assert health["default_strategy"] == "moving_average_trend"
    assert "interval_minutes" in health
