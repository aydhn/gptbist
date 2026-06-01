import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
from bist_signal_bot.app.healthcheck import SystemHealthCheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_monte_carlo():
    settings = Settings()
    hc = SystemHealthCheck(settings)

    res = hc.check()
    assert "monte_carlo" in res
    assert res["monte_carlo"]["status"] in ("ENABLED", "DISABLED")
    assert res["monte_carlo"]["resampling_capable"] is True
