import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
from bist_signal_bot.app.healthcheck import run_healthcheck

def test_healthcheck_contains_valuation():
    class MockSettings:
        ENABLE_VALUATION = True
        ENABLE_PORTFOLIO_LEDGER = False
        ENABLE_EVENT_CALENDAR = False
        ENABLE_FINANCIALS = False

    hc = run_healthcheck(MockSettings())
    assert "valuation" in hc
    assert hc["valuation"]["enabled"] is True
    assert hc["valuation"]["store_capable"] is True
