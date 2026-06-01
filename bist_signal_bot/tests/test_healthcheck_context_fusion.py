import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck

def test_healthcheck_includes_context_fusion():
    res = run_healthcheck()
    assert "context_fusion" in res
    assert res["context_fusion"]["enabled"] is True
