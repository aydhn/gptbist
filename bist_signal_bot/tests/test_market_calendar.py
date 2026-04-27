from datetime import date

import pytest

from bist_signal_bot.calendar.market_calendar import BistMarketCalendar
from bist_signal_bot.calendar.models import MarketDayType
from bist_signal_bot.core.exceptions import MarketCalendarError


@pytest.fixture
def calendar():
    return BistMarketCalendar(
        manual_holidays={date(2023, 1, 2)} # Monday holiday
    )

def test_is_weekend(calendar):
    assert calendar.is_weekend(date(2023, 1, 7)) is True # Saturday
    assert calendar.is_weekend(date(2023, 1, 8)) is True # Sunday
    assert calendar.is_weekend(date(2023, 1, 9)) is False # Monday

def test_get_day_type(calendar):
    assert calendar.get_day_type(date(2023, 1, 7)) == MarketDayType.WEEKEND
    assert calendar.get_day_type(date(2023, 1, 2)) == MarketDayType.HOLIDAY
    assert calendar.get_day_type(date(2023, 1, 3)) == MarketDayType.TRADING_DAY

def test_is_trading_day(calendar):
    assert calendar.is_trading_day(date(2023, 1, 3)) is True
    assert calendar.is_trading_day(date(2023, 1, 2)) is False
    assert calendar.is_trading_day(date(2023, 1, 7)) is False

def test_next_trading_day(calendar):
    # Jan 2 (Mon) is holiday, Jan 3 (Tue) is trading
    assert calendar.next_trading_day(date(2023, 1, 1)) == date(2023, 1, 3)
    # Friday -> Monday
    assert calendar.next_trading_day(date(2023, 1, 6)) == date(2023, 1, 9)

def test_previous_trading_day(calendar):
    # Jan 2 (Mon) is holiday, Dec 30 (Fri) is trading
    assert calendar.previous_trading_day(date(2023, 1, 3)) == date(2022, 12, 30)

def test_market_open_close_datetime(calendar):
    open_dt = calendar.market_open_datetime(date(2023, 1, 3))
    assert open_dt is not None
    assert open_dt.hour == 10

    close_dt = calendar.market_close_datetime(date(2023, 1, 3))
    assert close_dt is not None
    assert close_dt.hour == 18

def test_market_open_close_datetime_non_trading(calendar):
    assert calendar.market_open_datetime(date(2023, 1, 2)) is None
    assert calendar.market_close_datetime(date(2023, 1, 7)) is None

def test_trading_days_between(calendar):
    days = calendar.trading_days_between(date(2023, 1, 1), date(2023, 1, 4))
    # Jan 1 (Sun), Jan 2 (Hol), Jan 3 (Tue), Jan 4 (Wed)
    assert len(days) == 2
    assert days[0] == date(2023, 1, 3)
    assert days[1] == date(2023, 1, 4)

def test_trading_days_between_error(calendar):
    with pytest.raises(MarketCalendarError):
        calendar.trading_days_between(date(2023, 1, 4), date(2023, 1, 1))
