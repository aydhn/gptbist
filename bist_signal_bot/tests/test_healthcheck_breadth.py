import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_contains_breadth():
    settings = Settings()
    res = run_healthcheck(settings=settings)
    assert res["status"] == "pass"
    assert "breadth" in res
    assert res["breadth"]["enabled"] is True
    assert res["breadth"]["universe_builder_capable"] is True
