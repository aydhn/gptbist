import pytest
from datetime import datetime, time
from bist_signal_bot.scheduler.calendar import BISTMarketCalendar
from bist_signal_bot.scheduler.session import MarketSessionResolver
from bist_signal_bot.scheduler.models import MarketSessionType, MarketDayType

class MockSettings:
    pass

def test_market_session_closed_weekend(tmp_path):
    cal = BISTMarketCalendar(data_dir=tmp_path)
    res = MarketSessionResolver(cal, MockSettings())

    # Saturday noon
    dt = datetime(2025, 10, 25, 12, 0)
    snap = res.current_session(dt)

    assert snap.day_type == MarketDayType.WEEKEND
    assert snap.session_type == MarketSessionType.CLOSED
    assert snap.market_open is False

def test_market_session_intraday(tmp_path):
    cal = BISTMarketCalendar(data_dir=tmp_path)
    res = MarketSessionResolver(cal, MockSettings())

    # Friday noon
    dt = datetime(2025, 10, 24, 12, 0)
    snap = res.current_session(dt)

    assert snap.day_type == MarketDayType.TRADING_DAY
    assert snap.session_type == MarketSessionType.INTRADAY
    assert snap.market_open is True
