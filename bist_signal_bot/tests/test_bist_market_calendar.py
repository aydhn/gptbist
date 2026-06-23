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

from bist_signal_bot.core.exceptions import MarketCalendarError

def test_trading_days_between_normal():
    """Test trading_days_between returns correct trading days."""
    cal = BistMarketCalendar(
        manual_holidays={date(2024, 1, 1)}
    )
    # Start: 2023-12-29 (Friday)
    # 2023-12-30 (Saturday, Weekend)
    # 2023-12-31 (Sunday, Weekend)
    # 2024-01-01 (Monday, Holiday)
    # 2024-01-02 (Tuesday, Trading day)
    # 2024-01-03 (Wednesday, Trading day)
    start = date(2023, 12, 29)
    end = date(2024, 1, 3)

    days = cal.trading_days_between(start, end)

    assert len(days) == 3
    assert days[0] == date(2023, 12, 29)
    assert days[1] == date(2024, 1, 2)
    assert days[2] == date(2024, 1, 3)

def test_trading_days_between_invalid_dates():
    """Test trading_days_between raises MarketCalendarError when start > end."""
    cal = BistMarketCalendar()
    with pytest.raises(MarketCalendarError, match="Start date cannot be after end date."):
        cal.trading_days_between(date(2024, 1, 3), date(2024, 1, 1))

def test_trading_days_between_single_trading_day():
    """Test trading_days_between returns a single day when start and end are the same trading day."""
    cal = BistMarketCalendar()
    d = date(2024, 1, 2) # Tuesday
    days = cal.trading_days_between(d, d)
    assert len(days) == 1
    assert days[0] == d

def test_trading_days_between_single_non_trading_day():
    """Test trading_days_between returns empty list when start and end are the same non-trading day."""
    cal = BistMarketCalendar()
    d = date(2024, 1, 6) # Saturday
    days = cal.trading_days_between(d, d)
    assert len(days) == 0
