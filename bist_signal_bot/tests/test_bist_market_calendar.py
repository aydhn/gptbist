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

def test_bist_market_calendar_is_weekend():
    """Test is_weekend method correctly identifies weekends."""
    cal = BistMarketCalendar()

    # Weekdays
    assert cal.is_weekend(date(2023, 10, 2)) is False # Monday
    assert cal.is_weekend(date(2023, 10, 3)) is False # Tuesday
    assert cal.is_weekend(date(2023, 10, 4)) is False # Wednesday
    assert cal.is_weekend(date(2023, 10, 5)) is False # Thursday
    assert cal.is_weekend(date(2023, 10, 6)) is False # Friday

    # Weekends
    assert cal.is_weekend(date(2023, 10, 7)) is True # Saturday
    assert cal.is_weekend(date(2023, 10, 8)) is True # Sunday
