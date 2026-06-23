import pytest
from datetime import date
from unittest.mock import Mock

from bist_signal_bot.calendar.market_calendar import BistMarketCalendar
from bist_signal_bot.config.settings import Settings

def test_bist_market_calendar_from_settings():
    """Test from_settings method correctly initializes calendar from Settings."""
    settings = Settings(
        MARKET_TIMEZONE="Europe/London",
        BIST_REGULAR_OPEN="08:00",
        BIST_REGULAR_CLOSE="16:30",
        BIST_MANUAL_HOLIDAYS="2024-01-01,2024-12-25"
    )

    cal = BistMarketCalendar.from_settings(settings)

    assert cal.timezone_name == "Europe/London"
    assert cal.regular_open == "08:00"
    assert cal.regular_close == "16:30"
    assert len(cal.manual_holidays) == 2
    assert date(2024, 1, 1) in cal.manual_holidays
    assert date(2024, 12, 25) in cal.manual_holidays

def test_bist_market_calendar_from_settings_empty_holidays():
    """Test from_settings with empty holidays handles correctly."""
    settings = Settings(
        MARKET_TIMEZONE="America/New_York",
        BIST_REGULAR_OPEN="09:30",
        BIST_REGULAR_CLOSE="16:00",
        BIST_MANUAL_HOLIDAYS=""
    )

    cal = BistMarketCalendar.from_settings(settings)

    assert cal.timezone_name == "America/New_York"
    assert cal.regular_open == "09:30"
    assert cal.regular_close == "16:00"
    assert len(cal.manual_holidays) == 0

def test_previous_trading_day_normal():
    """Test previous_trading_day correctly identifies the previous weekday."""
    cal = BistMarketCalendar()

    # Oct 25 2024 is Friday
    current_date = date(2024, 10, 25)

    # Oct 24 2024 is Thursday
    prev_day = cal.previous_trading_day(current_date)
    assert prev_day == date(2024, 10, 24)

def test_previous_trading_day_over_weekend():
    """Test previous_trading_day skips weekends correctly."""
    cal = BistMarketCalendar()

    # Oct 28 2024 is Monday
    current_date = date(2024, 10, 28)

    # Previous trading day should be Friday, Oct 25
    prev_day = cal.previous_trading_day(current_date)
    assert prev_day == date(2024, 10, 25)

    # Oct 27 2024 is Sunday
    sunday_date = date(2024, 10, 27)

    # Previous trading day from Sunday should also be Friday, Oct 25
    prev_day_from_sunday = cal.previous_trading_day(sunday_date)
    assert prev_day_from_sunday == date(2024, 10, 25)

def test_previous_trading_day_skips_holidays():
    """Test previous_trading_day skips configured manual holidays."""
    holidays = {date(2024, 1, 1)} # Monday is a holiday
    cal = BistMarketCalendar(manual_holidays=holidays)

    # Jan 2 2024 is Tuesday
    current_date = date(2024, 1, 2)

    # Previous trading day should skip Monday (holiday) and weekend, landing on Friday, Dec 29 2023
    prev_day = cal.previous_trading_day(current_date)
    assert prev_day == date(2023, 12, 29)

def test_previous_trading_day_max_lookback_exceeded():
    """Test previous_trading_day returns None if max_lookback_days is exceeded."""
    holidays = {
        date(2024, 1, 1),
        date(2024, 1, 2),
        date(2024, 1, 3),
        date(2024, 1, 4),
        date(2024, 1, 5)
    }
    cal = BistMarketCalendar(manual_holidays=holidays)

    # Jan 8 2024 is Monday
    current_date = date(2024, 1, 8)

    # Set max_lookback_days to 3
    # Lookback:
    # 1 day: Jan 7 (Sunday)
    # 2 days: Jan 6 (Saturday)
    # 3 days: Jan 5 (Friday - Holiday)
    # Exceeded max_lookback_days
    prev_day = cal.previous_trading_day(current_date, max_lookback_days=3)
    assert prev_day is None
