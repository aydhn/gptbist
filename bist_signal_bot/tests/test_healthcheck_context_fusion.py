import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck

def test_healthcheck_includes_context_fusion():
    res = run_healthcheck()
    assert "context_fusion" in res
    assert res["context_fusion"]["enabled"] is True
