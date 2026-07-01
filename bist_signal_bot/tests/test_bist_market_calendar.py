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

def test_next_trading_day_normal():
    """Test next_trading_day returns the very next day when it is a trading day."""
    cal = BistMarketCalendar()
    # 2024-01-02 is Tuesday, next day is 2024-01-03 Wednesday
    current = date(2024, 1, 2)
    expected_next = date(2024, 1, 3)
    assert cal.next_trading_day(current) == expected_next

def test_next_trading_day_across_weekend():
    """Test next_trading_day correctly skips weekends."""
    cal = BistMarketCalendar()
    # 2024-01-05 is Friday, next day should be 2024-01-08 Monday
    current = date(2024, 1, 5)
    expected_next = date(2024, 1, 8)
    assert cal.next_trading_day(current) == expected_next

def test_next_trading_day_across_holiday():
    """Test next_trading_day correctly skips a manual holiday."""
    # 2024-01-03 Wednesday is a normal day
    # 2024-01-04 Thursday is a holiday
    # Next day should be 2024-01-05 Friday
    cal = BistMarketCalendar(manual_holidays={date(2024, 1, 4)})
    current = date(2024, 1, 3)
    expected_next = date(2024, 1, 5)
    assert cal.next_trading_day(current) == expected_next

def test_next_trading_day_across_weekend_and_holidays():
    """Test next_trading_day correctly skips combined weekends and holidays."""
    # 2024-01-05 Friday is holiday
    # 2024-01-06 Saturday is weekend
    # 2024-01-07 Sunday is weekend
    # 2024-01-08 Monday is holiday
    # Next day should be 2024-01-09 Tuesday
    holidays = {date(2024, 1, 5), date(2024, 1, 8)}
    cal = BistMarketCalendar(manual_holidays=holidays)
    current = date(2024, 1, 4) # Thursday
    expected_next = date(2024, 1, 9)
    assert cal.next_trading_day(current) == expected_next

def test_next_trading_day_limit_exceeded():
    """Test next_trading_day returns None if max_lookahead_days limit is reached."""
    # A long holiday from Friday to next Friday (8 days total counting weekend)
    holidays = {
        date(2024, 1, 5), date(2024, 1, 8), date(2024, 1, 9),
        date(2024, 1, 10), date(2024, 1, 11), date(2024, 1, 12)
    }
    cal = BistMarketCalendar(manual_holidays=holidays)
    current = date(2024, 1, 4) # Thursday
    # The next trading day is 2024-01-15 (Monday).
    # That is 11 days later. If max_lookahead_days=10, it should fail to find it and return None.
    assert cal.next_trading_day(current, max_lookahead_days=10) is None

def test_previous_trading_day_normal():
    """Test previous_trading_day returns the very previous day when it is a trading day."""
    cal = BistMarketCalendar()
    # 2024-01-03 is Wednesday, previous day is 2024-01-02 Tuesday
    current = date(2024, 1, 3)
    expected_prev = date(2024, 1, 2)
    assert cal.previous_trading_day(current) == expected_prev

def test_previous_trading_day_across_weekend():
    """Test previous_trading_day correctly skips weekends."""
    cal = BistMarketCalendar()
    # 2024-01-08 is Monday, previous day should be 2024-01-05 Friday
    current = date(2024, 1, 8)
    expected_prev = date(2024, 1, 5)
    assert cal.previous_trading_day(current) == expected_prev

def test_previous_trading_day_across_holiday():
    """Test previous_trading_day correctly skips a manual holiday."""
    # 2024-01-05 Friday is a normal day
    # 2024-01-04 Thursday is a holiday
    # Previous day should be 2024-01-03 Wednesday
    cal = BistMarketCalendar(manual_holidays={date(2024, 1, 4)})
    current = date(2024, 1, 5)
    expected_prev = date(2024, 1, 3)
    assert cal.previous_trading_day(current) == expected_prev

def test_previous_trading_day_across_weekend_and_holidays():
    """Test previous_trading_day correctly skips combined weekends and holidays."""
    # 2024-01-09 Tuesday is start day
    # 2024-01-08 Monday is holiday
    # 2024-01-07 Sunday is weekend
    # 2024-01-06 Saturday is weekend
    # 2024-01-05 Friday is holiday
    # Previous day should be 2024-01-04 Thursday
    holidays = {date(2024, 1, 5), date(2024, 1, 8)}
    cal = BistMarketCalendar(manual_holidays=holidays)
    current = date(2024, 1, 9) # Tuesday
    expected_prev = date(2024, 1, 4)
    assert cal.previous_trading_day(current) == expected_prev

def test_previous_trading_day_limit_exceeded():
    """Test previous_trading_day returns None if max_lookback_days limit is reached."""
    # A long holiday from Friday to next Friday
    holidays = {
        date(2024, 1, 5), date(2024, 1, 8), date(2024, 1, 9),
        date(2024, 1, 10), date(2024, 1, 11), date(2024, 1, 12)
    }
    cal = BistMarketCalendar(manual_holidays=holidays)
    current = date(2024, 1, 15) # Monday
    # The previous trading day is 2024-01-04 (Thursday).
    # That is 11 days earlier. If max_lookback_days=10, it should fail to find it and return None.
    assert cal.previous_trading_day(current, max_lookback_days=10) is None

def test_trading_days_between_normal():
    """Test trading_days_between returns the correct days."""
    cal = BistMarketCalendar()
    # Wednesday 2024-01-03 to Friday 2024-01-05
    start = date(2024, 1, 3)
    end = date(2024, 1, 5)
    expected = [date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5)]
    assert cal.trading_days_between(start, end) == expected

def test_trading_days_between_with_weekends_and_holidays():
    """Test trading_days_between excludes weekends and holidays."""
    holidays = {date(2024, 1, 5)} # Friday holiday
    cal = BistMarketCalendar(manual_holidays=holidays)

    # Thursday 2024-01-04 to Tuesday 2024-01-09
    start = date(2024, 1, 4)
    end = date(2024, 1, 9)
    # Excludes 5th (holiday), 6th (sat), 7th (sun)
    expected = [date(2024, 1, 4), date(2024, 1, 8), date(2024, 1, 9)]
    assert cal.trading_days_between(start, end) == expected

def test_trading_days_between_invalid_dates():
    """Test trading_days_between raises an error if start > end."""
    cal = BistMarketCalendar()
    from bist_signal_bot.core.exceptions import MarketCalendarError
    import pytest
    start = date(2024, 1, 5)
    end = date(2024, 1, 3)
    with pytest.raises(MarketCalendarError, match="Start date cannot be after end date."):
        cal.trading_days_between(start, end)

def test_previous_trading_day_with_mocked_is_trading_day():
    cal = BistMarketCalendar()
    with patch.object(cal, "is_trading_day", side_effect=[False, False, True]):
        d = date(2025, 1, 10)
        res = cal.previous_trading_day(d)
        assert res == date(2025, 1, 7)
        assert cal.is_trading_day.call_count == 3

def test_previous_trading_day_mock_limit_reached():
    cal = BistMarketCalendar()
    # Mock it so that it's always False for max_lookback_days
    with patch.object(cal, "is_trading_day", return_value=False):
        d = date(2025, 1, 10)
        res = cal.previous_trading_day(d, max_lookback_days=5)
        assert res is None
        assert cal.is_trading_day.call_count == 5

def test_previous_trading_day_mock_negative_lookback():
    cal = BistMarketCalendar()
    with patch.object(cal, "is_trading_day") as mock_is_trading_day:
        d = date(2025, 1, 10)
        res = cal.previous_trading_day(d, max_lookback_days=-1)
        assert res is None
        mock_is_trading_day.assert_not_called()

def test_previous_trading_day_mock_zero_lookback():
    cal = BistMarketCalendar()
    with patch.object(cal, "is_trading_day") as mock_is_trading_day:
        d = date(2025, 1, 10)
        res = cal.previous_trading_day(d, max_lookback_days=0)
        assert res is None
        mock_is_trading_day.assert_not_called()

def test_is_manual_holiday_true():
    cal = BistMarketCalendar(manual_holidays={date(2025, 10, 24)})
    assert cal.is_manual_holiday(date(2025, 10, 24)) is True

def test_is_manual_holiday_false():
    cal = BistMarketCalendar(manual_holidays={date(2025, 10, 24)})
    assert cal.is_manual_holiday(date(2025, 10, 25)) is False
