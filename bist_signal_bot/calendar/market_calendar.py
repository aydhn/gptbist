from datetime import date, datetime, timedelta

from bist_signal_bot.calendar.models import MarketDayType
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import MarketCalendarError
from bist_signal_bot.core.time_utils import combine_date_time_istanbul, parse_iso_date_list


class BistMarketCalendar:
    def __init__(
        self,
        timezone_name: str = "Europe/Istanbul",
        regular_open: str = "10:00",
        regular_close: str = "18:00",
        manual_holidays: set[date] | None = None
    ):
        self.timezone_name = timezone_name
        self.regular_open = regular_open
        self.regular_close = regular_close
        self.manual_holidays = manual_holidays or set()

    def is_weekend(self, day: date) -> bool:
        return day.weekday() >= 5

    def is_manual_holiday(self, day: date) -> bool:
        return day in self.manual_holidays

    def get_day_type(self, day: date) -> MarketDayType:
        if self.is_weekend(day):
            return MarketDayType.WEEKEND
        if self.is_manual_holiday(day):
            return MarketDayType.HOLIDAY
        return MarketDayType.TRADING_DAY

    def is_trading_day(self, day: date) -> bool:
        return self.get_day_type(day) == MarketDayType.TRADING_DAY

    def market_open_datetime(self, day: date) -> datetime | None:
        if not self.is_trading_day(day):
            return None
        return combine_date_time_istanbul(day, self.regular_open)

    def market_close_datetime(self, day: date) -> datetime | None:
        if not self.is_trading_day(day):
            return None
        return combine_date_time_istanbul(day, self.regular_close)

    def next_trading_day(self, day: date, max_lookahead_days: int = 15) -> date | None:
        current_day = day + timedelta(days=1)
        for _ in range(max_lookahead_days):
            if self.is_trading_day(current_day):
                return current_day
            current_day += timedelta(days=1)
        return None

    def previous_trading_day(self, day: date, max_lookback_days: int = 15) -> date | None:
        current_day = day - timedelta(days=1)
        for _ in range(max_lookback_days):
            if self.is_trading_day(current_day):
                return current_day
            current_day -= timedelta(days=1)
        return None

    def trading_days_between(self, start: date, end: date) -> list[date]:
        if start > end:
            raise MarketCalendarError("Start date cannot be after end date.")

        days = []
        current_day = start
        while current_day <= end:
            if self.is_trading_day(current_day):
                days.append(current_day)
            current_day += timedelta(days=1)
        return days

    @classmethod
    def from_settings(cls, settings: Settings) -> "BistMarketCalendar":
        holidays = parse_iso_date_list(settings.BIST_MANUAL_HOLIDAYS)
        return cls(
            timezone_name=settings.MARKET_TIMEZONE,
            regular_open=settings.BIST_REGULAR_OPEN,
            regular_close=settings.BIST_REGULAR_CLOSE,
            manual_holidays=holidays
        )
