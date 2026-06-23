import pytest
from datetime import datetime, date
from pathlib import Path
from unittest.mock import patch

from bist_signal_bot.scheduler.calendar import BISTMarketCalendar as SchedulerMarketCalendar
from bist_signal_bot.scheduler.models import MarketDayType as SchedulerMarketDayType
from bist_signal_bot.calendar.market_calendar import BistMarketCalendar
from bist_signal_bot.calendar.models import MarketDayType

def test_market_calendar_default_weekend(tmp_path):
    cal = SchedulerMarketCalendar(data_dir=tmp_path)

    # Oct 25 2025 is a Saturday
    dt = datetime(2025, 10, 25)
    day = cal.get_day(dt)
    assert day.day_type == SchedulerMarketDayType.WEEKEND

def test_market_calendar_default_trading(tmp_path):
    cal = SchedulerMarketCalendar(data_dir=tmp_path)

    # Oct 24 2025 is a Friday
    dt = datetime(2025, 10, 24)
    day = cal.get_day(dt)
    assert day.day_type == SchedulerMarketDayType.TRADING_DAY

def test_market_calendar_next_trading_day(tmp_path):
    cal = SchedulerMarketCalendar(data_dir=tmp_path)

    # Oct 24 2025 is a Friday, next should be Monday 27th
    dt = datetime(2025, 10, 24)
    next_day = cal.next_trading_day(dt)
    assert next_day.date.date() == date(2025, 10, 27)

def test_market_open_datetime():
    cal = BistMarketCalendar(regular_open="10:00")

    # Oct 24, 2025 is a Friday (trading day)
    dt = date(2025, 10, 24)
    with patch("bist_signal_bot.core.time_utils.get_settings") as mock_settings:
        from bist_signal_bot.config.settings import Settings
        mock_settings.return_value = Settings(MARKET_TIMEZONE="Europe/Istanbul")
        open_dt = cal.market_open_datetime(dt)

        assert open_dt is not None
        assert open_dt.year == 2025
        assert open_dt.month == 10
        assert open_dt.day == 24
        assert open_dt.hour == 10
        assert open_dt.minute == 0
        assert open_dt.tzinfo is not None

def test_market_open_datetime_weekend():
    cal = BistMarketCalendar()

    # Oct 25, 2025 is a Saturday (weekend)
    dt = date(2025, 10, 25)
    open_dt = cal.market_open_datetime(dt)

    assert open_dt is None

def test_market_open_datetime_manual_holiday():
    dt = date(2025, 10, 24)
    cal = BistMarketCalendar(manual_holidays={dt})

    open_dt = cal.market_open_datetime(dt)

    assert open_dt is None

def test_market_close_datetime():
    cal = BistMarketCalendar(regular_close="18:00")

    # Oct 24, 2025 is a Friday (trading day)
    dt = date(2025, 10, 24)
    with patch("bist_signal_bot.core.time_utils.get_settings") as mock_settings:
        from bist_signal_bot.config.settings import Settings
        mock_settings.return_value = Settings(MARKET_TIMEZONE="Europe/Istanbul")
        close_dt = cal.market_close_datetime(dt)

        assert close_dt is not None
        assert close_dt.year == 2025
        assert close_dt.month == 10
        assert close_dt.day == 24
        assert close_dt.hour == 18
        assert close_dt.minute == 0
        assert close_dt.tzinfo is not None

def test_market_close_datetime_weekend():
    cal = BistMarketCalendar()

    # Oct 25, 2025 is a Saturday (weekend)
    dt = date(2025, 10, 25)
    close_dt = cal.market_close_datetime(dt)

    assert close_dt is None

def test_market_close_datetime_manual_holiday():
    dt = date(2025, 10, 24)
    cal = BistMarketCalendar(manual_holidays={dt})

    close_dt = cal.market_close_datetime(dt)

    assert close_dt is None

def test_trading_days_between():
    cal = BistMarketCalendar()

    # Oct 24, 2025 is Friday
    # Oct 25, 2025 is Saturday
    # Oct 26, 2025 is Sunday
    # Oct 27, 2025 is Monday
    start_dt = date(2025, 10, 24)
    end_dt = date(2025, 10, 27)

    days = cal.trading_days_between(start_dt, end_dt)

    assert len(days) == 2
    assert days[0] == date(2025, 10, 24)
    assert days[1] == date(2025, 10, 27)

def test_trading_days_between_error():
    cal = BistMarketCalendar()
    from bist_signal_bot.core.exceptions import MarketCalendarError
    with pytest.raises(MarketCalendarError):
        cal.trading_days_between(date(2025, 10, 27), date(2025, 10, 24))

def test_from_settings():
    from bist_signal_bot.config.settings import Settings
    settings = Settings(
        MARKET_TIMEZONE="Europe/Istanbul",
        BIST_REGULAR_OPEN="10:00",
        BIST_REGULAR_CLOSE="18:00",
        BIST_MANUAL_HOLIDAYS="2025-10-24,2025-10-29"
    )

    cal = BistMarketCalendar.from_settings(settings)

    assert cal.timezone_name == "Europe/Istanbul"
    assert cal.regular_open == "10:00"
    assert cal.regular_close == "18:00"
    assert len(cal.manual_holidays) == 2
    assert date(2025, 10, 24) in cal.manual_holidays
    assert date(2025, 10, 29) in cal.manual_holidays

def test_next_trading_day_limit():
    cal = BistMarketCalendar()
    # Looking for next trading day starting from a Saturday
    dt = date(2025, 10, 25)
    # If we limit lookahead to 0, it should fail
    next_day = cal.next_trading_day(dt, max_lookahead_days=0)
    assert next_day is None

def test_previous_trading_day_limit():
    cal = BistMarketCalendar()
    # Looking for previous trading day starting from a Sunday
    dt = date(2025, 10, 26)
    # If we limit lookback to 0, it should fail
    prev_day = cal.previous_trading_day(dt, max_lookback_days=0)
    assert prev_day is None

def test_previous_trading_day():
    cal = BistMarketCalendar()
    # Looking for previous trading day starting from a Monday
    dt = date(2025, 10, 27)
    # Should be the previous Friday
    prev_day = cal.previous_trading_day(dt)
    assert prev_day == date(2025, 10, 24)


def test_get_day_type_holiday():
    dt = date(2025, 10, 24)
    cal = BistMarketCalendar(manual_holidays={dt})
    assert cal.get_day_type(dt) == MarketDayType.HOLIDAY


def test_next_trading_day():
    cal = BistMarketCalendar()
    # Looking for next trading day starting from a Friday
    dt = date(2025, 10, 24)
    # Should be the next Monday
    next_day = cal.next_trading_day(dt)
    assert next_day == date(2025, 10, 27)

def test_previous_trading_day_skip_holiday():
    dt = date(2025, 10, 24) # Friday
    cal = BistMarketCalendar(manual_holidays={dt})
    # Start looking from Monday, Oct 27
    start_dt = date(2025, 10, 27)
    # Since Friday is holiday, previous trading day should be Thursday, Oct 23
    prev_day = cal.previous_trading_day(start_dt)
    assert prev_day == date(2025, 10, 23)

def test_previous_trading_day_max_lookback_exceeded_due_to_holiday():
    # Thursday to Tuesday are holidays
    holidays = {
        date(2025, 10, 23),
        date(2025, 10, 24),
        date(2025, 10, 27),
        date(2025, 10, 28)
    }
    cal = BistMarketCalendar(manual_holidays=holidays)
    # Start looking from Wednesday, Oct 29
    start_dt = date(2025, 10, 29)
    # Limit to 3 days lookback. It will check Oct 28 (holiday), Oct 27 (holiday), Oct 26 (weekend).
    # Then it exceeds max_lookback_days (which is 3) and returns None.
    prev_day = cal.previous_trading_day(start_dt, max_lookback_days=3)
    assert prev_day is None
