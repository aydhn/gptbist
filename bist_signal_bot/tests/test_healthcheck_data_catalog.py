import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck

def test_healthcheck_includes_data_catalog():
    res = run_healthcheck()
    assert "data_catalog" in res
    assert res["data_catalog"]["enabled"] is True
