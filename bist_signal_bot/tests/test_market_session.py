from datetime import date, datetime

import pytest

from bist_signal_bot.calendar.market_calendar import BistMarketCalendar
from bist_signal_bot.calendar.models import MarketSessionType
from bist_signal_bot.calendar.session import BistMarketSessionService
from bist_signal_bot.core.time_utils import ensure_istanbul_timezone


@pytest.fixture
def session_service():
    calendar = BistMarketCalendar(manual_holidays={date(2023, 1, 2)})
    return BistMarketSessionService(
        calendar=calendar,
        signal_after_close_minutes=15,
        intraday_signal_enabled=True,
        daily_signal_enabled=True
    )

def _dt(year, month, day, hour, minute):
    return ensure_istanbul_timezone(datetime(year, month, day, hour, minute))

def test_session_status_pre_market(session_service):
    dt = _dt(2023, 1, 3, 9, 0)
    status = session_service.get_status(dt)
    assert status.session_type == MarketSessionType.PRE_MARKET
    assert not status.is_market_open

def test_session_status_regular(session_service):
    dt = _dt(2023, 1, 3, 14, 0)
    status = session_service.get_status(dt)
    assert status.session_type == MarketSessionType.REGULAR
    assert status.is_market_open

def test_session_status_post_market(session_service):
    dt = _dt(2023, 1, 3, 18, 30)
    status = session_service.get_status(dt)
    assert status.session_type == MarketSessionType.POST_MARKET
    assert not status.is_market_open

def test_session_status_holiday(session_service):
    dt = _dt(2023, 1, 2, 14, 0)
    status = session_service.get_status(dt)
    assert status.session_type == MarketSessionType.HOLIDAY
    assert not status.is_market_open

def test_session_status_weekend(session_service):
    dt = _dt(2023, 1, 7, 14, 0) # Saturday
    status = session_service.get_status(dt)
    assert status.session_type == MarketSessionType.WEEKEND
    assert not status.is_market_open

def test_should_generate_intraday_signal(session_service):
    assert session_service.should_generate_intraday_signal(_dt(2023, 1, 3, 14, 0)) is True
    assert session_service.should_generate_intraday_signal(_dt(2023, 1, 3, 9, 0)) is False

    session_service.intraday_signal_enabled = False
    assert session_service.should_generate_intraday_signal(_dt(2023, 1, 3, 14, 0)) is False

def test_should_generate_daily_signal(session_service):
    # Close is 18:00, wait is 15 mins -> 18:15
    assert session_service.should_generate_daily_signal(_dt(2023, 1, 3, 18, 14)) is False
    assert session_service.should_generate_daily_signal(_dt(2023, 1, 3, 18, 15)) is True
    assert session_service.should_generate_daily_signal(_dt(2023, 1, 3, 19, 0)) is True

    # Not on a holiday
    assert session_service.should_generate_daily_signal(_dt(2023, 1, 2, 19, 0)) is False

    session_service.daily_signal_enabled = False
    assert session_service.should_generate_daily_signal(_dt(2023, 1, 3, 19, 0)) is False
