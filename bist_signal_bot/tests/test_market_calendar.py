import pytest
from datetime import datetime, date
from pathlib import Path
from bist_signal_bot.scheduler.calendar import BISTMarketCalendar
from bist_signal_bot.scheduler.models import MarketDayType as SchedulerMarketDayType
from bist_signal_bot.calendar.models import MarketDayType

from bist_signal_bot.calendar.market_calendar import BistMarketCalendar


def test_market_calendar_default_weekend(tmp_path):
    cal = BISTMarketCalendar(data_dir=tmp_path)

    # Oct 25 2025 is a Saturday
    dt = datetime(2025, 10, 25)
    day = cal.get_day(dt)
    assert day.day_type == SchedulerMarketDayType.WEEKEND

def test_market_calendar_default_trading(tmp_path):
    cal = BISTMarketCalendar(data_dir=tmp_path)

    # Oct 24 2025 is a Friday
    dt = datetime(2025, 10, 24)
    day = cal.get_day(dt)
    assert day.day_type == SchedulerMarketDayType.TRADING_DAY

def test_market_calendar_next_trading_day(tmp_path):
    cal = BISTMarketCalendar(data_dir=tmp_path)

    # Oct 24 2025 is a Friday, next should be Monday 27th
    dt = datetime(2025, 10, 24)
    next_day = cal.next_trading_day(dt)
    assert next_day.date.date() == date(2025, 10, 27)

def test_get_day_type_weekend():
    cal = BistMarketCalendar()
    # Oct 25 2025 is a Saturday
    day = date(2025, 10, 25)
    assert cal.get_day_type(day) == MarketDayType.WEEKEND

def test_get_day_type_holiday():
    holiday = date(2025, 1, 1)
    cal = BistMarketCalendar(manual_holidays={holiday})
    assert cal.get_day_type(holiday) == MarketDayType.HOLIDAY

def test_get_day_type_trading_day():
    cal = BistMarketCalendar()
    # Oct 24 2025 is a Friday
    day = date(2025, 10, 24)
    assert cal.get_day_type(day) == MarketDayType.TRADING_DAY
