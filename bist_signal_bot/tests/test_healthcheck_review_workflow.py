import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
from bist_signal_bot.app.healthcheck import run_healthcheck

def test_healthcheck_review_workflow():
    result = run_healthcheck()
    assert result["status"] in ("healthy", "pass")
    assert "review_workflow" in result
    assert result["review_workflow"]["enabled"] == True
