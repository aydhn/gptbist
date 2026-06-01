import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings
from unittest.mock import patch

def test_healthcheck_includes_portfolio_risk():
    settings = Settings()
    hc = run_healthcheck(settings)
    assert "portfolio_risk_engine" in hc
    assert hc["portfolio_risk_engine"]["status"] == "healthy"
