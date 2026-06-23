import pytest
from datetime import date
from unittest.mock import Mock, patch

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

def test_market_close_datetime_trading_day():
    """Test market_close_datetime returns correct datetime for a trading day."""
    cal = BistMarketCalendar(
        timezone_name="Europe/Istanbul",
        regular_close="18:00"
    )
    # A known trading day (assuming it's not a manual holiday)
    # 2024-01-02 was a Tuesday
    d = date(2024, 1, 2)
    with patch("bist_signal_bot.core.time_utils.get_settings") as mock_settings:
        mock_settings.return_value.MARKET_TIMEZONE = "Europe/Istanbul"
        dt = cal.market_close_datetime(d)
    assert dt is not None
    assert dt.year == 2024
    assert dt.month == 1
    assert dt.day == 2
    assert dt.hour == 18
    assert dt.minute == 0
    assert dt.tzinfo is not None

def test_market_close_datetime_non_trading_day():
    """Test market_close_datetime returns None for a non-trading day."""
    cal = BistMarketCalendar(
        manual_holidays={date(2024, 1, 1)}
    )
    # Weekend
    assert cal.market_close_datetime(date(2024, 1, 6)) is None
    # Holiday
    assert cal.market_close_datetime(date(2024, 1, 1)) is None

def test_market_open_datetime_trading_day():
    """Test market_open_datetime returns correct datetime for a trading day."""
    cal = BistMarketCalendar(
        timezone_name="Europe/Istanbul",
        regular_open="10:00"
    )
    d = date(2024, 1, 2)
    with patch("bist_signal_bot.core.time_utils.get_settings") as mock_settings:
        mock_settings.return_value.MARKET_TIMEZONE = "Europe/Istanbul"
        dt = cal.market_open_datetime(d)
    assert dt is not None
    assert dt.year == 2024
    assert dt.month == 1
    assert dt.day == 2
    assert dt.hour == 10
    assert dt.minute == 0
    assert dt.tzinfo is not None

def test_market_open_datetime_non_trading_day():
    """Test market_open_datetime returns None for a non-trading day."""
    cal = BistMarketCalendar(
        manual_holidays={date(2024, 1, 1)}
    )
    # Weekend
    assert cal.market_open_datetime(date(2024, 1, 6)) is None
    # Holiday
    assert cal.market_open_datetime(date(2024, 1, 1)) is None

def test_is_trading_day_regular():
    """Test is_trading_day returns True for a regular trading day."""
    cal = BistMarketCalendar()
    # 2024-01-02 was a Tuesday
    assert cal.is_trading_day(date(2024, 1, 2)) is True

def test_is_trading_day_weekend():
    """Test is_trading_day returns False for a weekend."""
    cal = BistMarketCalendar()
    # 2024-01-06 was a Saturday
    assert cal.is_trading_day(date(2024, 1, 6)) is False

def test_is_trading_day_holiday():
    """Test is_trading_day returns False for a manual holiday."""
    holiday_date = date(2024, 1, 1)
    cal = BistMarketCalendar(manual_holidays={holiday_date})
    # 2024-01-01 was a Monday but marked as holiday
    assert cal.is_trading_day(holiday_date) is False
