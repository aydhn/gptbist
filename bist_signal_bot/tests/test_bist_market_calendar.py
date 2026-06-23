import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch
from bist_signal_bot.calendar.market_calendar import BistMarketCalendar
from bist_signal_bot.calendar.models import MarketDayType
from bist_signal_bot.core.exceptions import MarketCalendarError

def test_get_day_type():
    # Setup test scenarios
    holiday = date(2023, 10, 27) # Republic Day mock (using Friday to avoid weekend logic)
    cal = BistMarketCalendar(manual_holidays={holiday})

    # Test weekday (Monday)
    assert cal.get_day_type(date(2023, 10, 2)) == MarketDayType.TRADING_DAY

    # Test weekend (Saturday)
    assert cal.get_day_type(date(2023, 10, 28)) == MarketDayType.WEEKEND

    # Test weekend (Sunday)
    assert cal.get_day_type(date(2023, 10, 1)) == MarketDayType.WEEKEND

    # Test manual holiday
    assert cal.get_day_type(holiday) == MarketDayType.HOLIDAY

def test_is_weekend():
    cal = BistMarketCalendar()
    assert cal.is_weekend(date(2023, 10, 28)) is True   # Saturday
    assert cal.is_weekend(date(2023, 10, 29)) is True   # Sunday
    assert cal.is_weekend(date(2023, 10, 30)) is False  # Monday

def test_is_manual_holiday():
    holiday = date(2023, 10, 27)
    cal = BistMarketCalendar(manual_holidays={holiday})
    assert cal.is_manual_holiday(holiday) is True
    assert cal.is_manual_holiday(date(2023, 10, 26)) is False

def test_is_trading_day():
    holiday = date(2023, 10, 27)
    cal = BistMarketCalendar(manual_holidays={holiday})
    assert cal.is_trading_day(date(2023, 10, 26)) is True   # Thursday
    assert cal.is_trading_day(date(2023, 10, 27)) is False  # Holiday
    assert cal.is_trading_day(date(2023, 10, 28)) is False  # Saturday

@patch('bist_signal_bot.core.time_utils.get_settings')
def test_market_open_datetime(mock_get_settings):
    mock_get_settings.return_value.MARKET_TIMEZONE = "Europe/Istanbul"
    cal = BistMarketCalendar(regular_open="10:00")
    dt = date(2023, 10, 26)  # Thursday
    res = cal.market_open_datetime(dt)
    assert res is not None
    assert res.hour == 10
    assert res.minute == 0

    # weekend
    assert cal.market_open_datetime(date(2023, 10, 28)) is None

@patch('bist_signal_bot.core.time_utils.get_settings')
def test_market_close_datetime(mock_get_settings):
    mock_get_settings.return_value.MARKET_TIMEZONE = "Europe/Istanbul"
    cal = BistMarketCalendar(regular_close="18:00")
    dt = date(2023, 10, 26)  # Thursday
    res = cal.market_close_datetime(dt)
    assert res is not None
    assert res.hour == 18
    assert res.minute == 0

    # weekend
    assert cal.market_close_datetime(date(2023, 10, 28)) is None

def test_next_trading_day():
    holiday = date(2023, 10, 27) # Friday
    cal = BistMarketCalendar(manual_holidays={holiday})

    # Next after Thursday (Oct 26) -> should skip Friday (holiday) and weekend -> Monday (Oct 30)
    next_day = cal.next_trading_day(date(2023, 10, 26))
    assert next_day == date(2023, 10, 30)

    # test beyond max_lookahead
    assert cal.next_trading_day(date(2023, 10, 26), max_lookahead_days=2) is None

def test_previous_trading_day():
    holiday = date(2023, 10, 27) # Friday
    cal = BistMarketCalendar(manual_holidays={holiday})

    # Previous before Monday (Oct 30) -> should skip weekend and Friday (holiday) -> Thursday (Oct 26)
    prev_day = cal.previous_trading_day(date(2023, 10, 30))
    assert prev_day == date(2023, 10, 26)

    # test beyond max_lookback
    assert cal.previous_trading_day(date(2023, 10, 30), max_lookback_days=2) is None

def test_trading_days_between():
    holiday = date(2023, 10, 27) # Friday
    cal = BistMarketCalendar(manual_holidays={holiday})

    # Wednesday to Tuesday
    # 25: Wed (Trading)
    # 26: Thu (Trading)
    # 27: Fri (Holiday)
    # 28: Sat (Weekend)
    # 29: Sun (Weekend)
    # 30: Mon (Trading)
    # 31: Tue (Trading)
    start_dt = date(2023, 10, 25)
    end_dt = date(2023, 10, 31)

    days = cal.trading_days_between(start_dt, end_dt)
    assert days == [
        date(2023, 10, 25),
        date(2023, 10, 26),
        date(2023, 10, 30),
        date(2023, 10, 31)
    ]

    with pytest.raises(MarketCalendarError):
        cal.trading_days_between(end_dt, start_dt)

@patch('bist_signal_bot.calendar.market_calendar.parse_iso_date_list')
def test_from_settings(mock_parse_iso):
    from bist_signal_bot.config.settings import Settings

    mock_parse_iso.return_value = {date(2023, 10, 29)}
    settings = Settings(
        MARKET_TIMEZONE="Europe/Istanbul",
        BIST_REGULAR_OPEN="09:40",
        BIST_REGULAR_CLOSE="18:10",
        BIST_MANUAL_HOLIDAYS="2023-10-29"
    )

    cal = BistMarketCalendar.from_settings(settings)
    assert cal.timezone_name == "Europe/Istanbul"
    assert cal.regular_open == "09:40"
    assert cal.regular_close == "18:10"
    assert date(2023, 10, 29) in cal.manual_holidays
