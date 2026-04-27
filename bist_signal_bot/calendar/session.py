from datetime import datetime, timedelta

from bist_signal_bot.calendar.market_calendar import BistMarketCalendar
from bist_signal_bot.calendar.models import MarketDayType, MarketSessionStatus, MarketSessionType
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.time_utils import ensure_istanbul_timezone, istanbul_now


class BistMarketSessionService:
    def __init__(
        self,
        calendar: BistMarketCalendar,
        signal_after_close_minutes: int = 15,
        intraday_signal_enabled: bool = False,
        daily_signal_enabled: bool = True
    ):
        self.calendar = calendar
        self.signal_after_close_minutes = signal_after_close_minutes
        self.intraday_signal_enabled = intraday_signal_enabled
        self.daily_signal_enabled = daily_signal_enabled

    def get_status(self, now: datetime | None = None) -> MarketSessionStatus:
        if now is None:
            now = istanbul_now()
        else:
            now = ensure_istanbul_timezone(now)

        day = now.date()
        day_type = self.calendar.get_day_type(day)
        is_trading_day = self.calendar.is_trading_day(day)

        market_open = self.calendar.market_open_datetime(day)
        market_close = self.calendar.market_close_datetime(day)

        session_type = MarketSessionType.UNKNOWN
        is_market_open = False
        message = ""

        if not is_trading_day:
            if day_type == MarketDayType.WEEKEND:
                session_type = MarketSessionType.WEEKEND
                message = "Market is closed for the weekend."
            elif day_type == MarketDayType.HOLIDAY:
                session_type = MarketSessionType.HOLIDAY
                message = "Market is closed for a holiday."
            else:
                session_type = MarketSessionType.CLOSED
                message = "Market is closed."
        else:
            if market_open and market_close:
                if now < market_open:
                    session_type = MarketSessionType.PRE_MARKET
                    message = "Market is in pre-market session."
                elif now >= market_close:
                    session_type = MarketSessionType.POST_MARKET
                    message = "Market is in post-market session."
                else:
                    session_type = MarketSessionType.REGULAR
                    is_market_open = True
                    message = "Market is open."
            else:
                session_type = MarketSessionType.CLOSED
                message = "Market hours not defined for today."

        next_trading_day = self.calendar.next_trading_day(day)
        previous_trading_day = self.calendar.previous_trading_day(day)

        return MarketSessionStatus(
            now=now,
            timezone=self.calendar.timezone_name,
            is_trading_day=is_trading_day,
            is_market_open=is_market_open,
            day_type=day_type,
            session_type=session_type,
            market_open=market_open,
            market_close=market_close,
            next_trading_day=next_trading_day,
            previous_trading_day=previous_trading_day,
            message=message
        )

    def is_market_open(self, now: datetime | None = None) -> bool:
        status = self.get_status(now)
        return status.is_market_open

    def should_generate_intraday_signal(self, now: datetime | None = None) -> bool:
        if not self.intraday_signal_enabled:
            return False
        return self.is_market_open(now)

    def should_generate_daily_signal(self, now: datetime | None = None) -> bool:
        if not self.daily_signal_enabled:
            return False

        status = self.get_status(now)
        if not status.is_trading_day:
            return False

        if status.market_close:
            target_time = status.market_close + timedelta(minutes=self.signal_after_close_minutes)
            return status.now >= target_time

        return False

    def should_send_daily_report(self, now: datetime | None = None) -> bool:
        # Currently same logic as daily signal
        return self.should_generate_daily_signal(now)

    @classmethod
    def from_settings(cls, settings: Settings) -> "BistMarketSessionService":
        calendar = BistMarketCalendar.from_settings(settings)
        return cls(
            calendar=calendar,
            signal_after_close_minutes=settings.BIST_SIGNAL_AFTER_CLOSE_MINUTES,
            intraday_signal_enabled=settings.BIST_INTRADAY_SIGNAL_ENABLED,
            daily_signal_enabled=settings.BIST_DAILY_SIGNAL_ENABLED
        )
