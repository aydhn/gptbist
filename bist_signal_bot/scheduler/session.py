from datetime import datetime, time, date
import logging
from typing import Optional

from bist_signal_bot.scheduler.models import (
    MarketSessionSnapshot,
    MarketSessionType,
    MarketDayType,
    ScheduledJob,
    MarketCalendarDay
)
from bist_signal_bot.scheduler.calendar import BISTMarketCalendar

logger = logging.getLogger(__name__)

class MarketSessionResolver:
    def __init__(self, calendar: BISTMarketCalendar, settings=None):
        self.calendar = calendar

        # Default BIST times if not in settings
        self.pre_market_start = time(8, 30)
        self.opening_start = time(9, 40)
        self.intraday_start = time(10, 0)
        self.closing_start = time(18, 0)
        self.post_market_start = time(18, 10)
        self.after_hours_start = time(18, 30)

        self.half_day_close = time(12, 40)

        # Load from settings if available
        if settings:
            try:
                def parse_time(s): return datetime.strptime(s, "%H:%M").time() if s else None

                self.pre_market_start = parse_time(getattr(settings, 'BIST_PRE_MARKET_START', None)) or self.pre_market_start
                self.opening_start = parse_time(getattr(settings, 'BIST_OPENING_START', None)) or self.opening_start
                self.intraday_start = parse_time(getattr(settings, 'BIST_INTRADAY_START', None)) or self.intraday_start
                self.closing_start = parse_time(getattr(settings, 'BIST_CLOSING_START', None)) or self.closing_start
                self.post_market_start = parse_time(getattr(settings, 'BIST_POST_MARKET_START', None)) or self.post_market_start
                self.after_hours_start = parse_time(getattr(settings, 'BIST_AFTER_HOURS_START', None)) or self.after_hours_start
                self.half_day_close = parse_time(getattr(settings, 'BIST_HALF_DAY_CLOSE_TIME', None)) or self.half_day_close
            except ValueError as e:
                logger.warning(f"Failed to parse time from settings, using defaults: {e}")

    def _parse_time_str(self, t_str: str | None, default: time) -> time:
        if not t_str:
            return default
        try:
            return datetime.strptime(t_str, "%H:%M").time()
        except ValueError:
            return default

    def current_session(self, now: datetime | None = None) -> MarketSessionSnapshot:
        if now is None:
            now = datetime.now()

        calendar_day = self.calendar.get_day(now)
        session_type = self.session_for_time(now, calendar_day)

        market_open = session_type in (MarketSessionType.OPENING, MarketSessionType.INTRADAY, MarketSessionType.CLOSING)

        return MarketSessionSnapshot(
            generated_at=datetime.utcnow(),
            local_date=now,
            timezone="Europe/Istanbul", # default assumption
            day_type=calendar_day.day_type,
            session_type=session_type,
            market_open=market_open,
            next_open_at=self.next_open(now),
            next_close_at=self.next_close(now),
        )

    def session_for_time(self, now: datetime, calendar_day: MarketCalendarDay) -> MarketSessionType:
        if calendar_day.day_type in (MarketDayType.HOLIDAY, MarketDayType.WEEKEND):
            return MarketSessionType.CLOSED

        t = now.time()

        is_half_day = calendar_day.day_type == MarketDayType.HALF_DAY

        # Override with calendar specific times if available
        open_t = self._parse_time_str(calendar_day.open_time, self.intraday_start)

        if is_half_day:
            close_t = self._parse_time_str(calendar_day.half_day_close_time, self.half_day_close)
            # Adjust ranges for half day
            post_market_t = (datetime.combine(date.today(), close_t) + (datetime.combine(date.today(), self.post_market_start) - datetime.combine(date.today(), self.closing_start))).time()
            after_hours_t = (datetime.combine(date.today(), close_t) + (datetime.combine(date.today(), self.after_hours_start) - datetime.combine(date.today(), self.closing_start))).time()
            closing_t = (datetime.combine(date.today(), close_t) - (datetime.combine(date.today(), self.closing_start) - datetime.combine(date.today(), self.intraday_start))).time()
            # simplify half day logic for now, standardizing to a simple cut-off
            if t < self.pre_market_start:
                return MarketSessionType.CLOSED
            elif t < self.opening_start:
                return MarketSessionType.PRE_MARKET
            elif t < open_t:
                return MarketSessionType.OPENING
            elif t < close_t:
                return MarketSessionType.INTRADAY
            else:
                return MarketSessionType.AFTER_HOURS # Simplify half day post sessions
        else:
            close_t = self._parse_time_str(calendar_day.close_time, self.closing_start)

            if t < self.pre_market_start:
                return MarketSessionType.CLOSED
            elif t < self.opening_start:
                return MarketSessionType.PRE_MARKET
            elif t < open_t:
                return MarketSessionType.OPENING
            elif t < close_t:
                return MarketSessionType.INTRADAY
            elif t < self.post_market_start:
                return MarketSessionType.CLOSING
            elif t < self.after_hours_start:
                return MarketSessionType.POST_MARKET
            else:
                return MarketSessionType.AFTER_HOURS

    def next_open(self, now: datetime) -> datetime | None:
        calendar_day = self.calendar.get_day(now)
        t = now.time()

        open_t = self._parse_time_str(calendar_day.open_time, self.intraday_start)

        if calendar_day.day_type in (MarketDayType.TRADING_DAY, MarketDayType.HALF_DAY) and t < open_t:
            return datetime.combine(now.date(), open_t)

        next_day = self.calendar.next_trading_day(now)
        next_open_t = self._parse_time_str(next_day.open_time, self.intraday_start)
        return datetime.combine(next_day.date.date(), next_open_t)

    def next_close(self, now: datetime) -> datetime | None:
        calendar_day = self.calendar.get_day(now)
        t = now.time()

        if calendar_day.day_type == MarketDayType.HALF_DAY:
            close_t = self._parse_time_str(calendar_day.half_day_close_time, self.half_day_close)
        else:
            close_t = self._parse_time_str(calendar_day.close_time, self.closing_start)

        if calendar_day.day_type in (MarketDayType.TRADING_DAY, MarketDayType.HALF_DAY) and t < close_t:
            return datetime.combine(now.date(), close_t)

        next_day = self.calendar.next_trading_day(now)
        if next_day.day_type == MarketDayType.HALF_DAY:
            next_close_t = self._parse_time_str(next_day.half_day_close_time, self.half_day_close)
        else:
            next_close_t = self._parse_time_str(next_day.close_time, self.closing_start)
        return datetime.combine(next_day.date.date(), next_close_t)

    def allowed_for_job(self, job: ScheduledJob, snapshot: MarketSessionSnapshot) -> tuple[bool, str]:
        if job.requires_market_open and not snapshot.market_open:
            return False, "Job requires market to be open"

        if not job.allow_after_hours and snapshot.session_type in (MarketSessionType.AFTER_HOURS, MarketSessionType.CLOSED):
            return False, "Job does not allow after hours execution"

        return True, "Allowed"
