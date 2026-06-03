from datetime import datetime, timedelta
from typing import List
from bist_signal_bot.markets.models import MarketCalendarDay, MarketSessionStatus

class MarketCalendarProvider:
    def __init__(self, store=None):
        self.store = store

    def default_calendar(self, market_id: str, start_date: str, end_date: str) -> List[MarketCalendarDay]:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = []
        curr = start
        while curr <= end:
            d_str = curr.strftime("%Y-%m-%d")
            status = MarketSessionStatus.REGULAR
            warnings = []
            if market_id == "CRYPTO_RESEARCH":
                warnings.append("24/7 crypto research fixture. No live guarantee.")
            elif curr.weekday() >= 5:
                status = MarketSessionStatus.CLOSED

            days.append(MarketCalendarDay(
                day_id=f"{market_id}_{d_str}",
                market_id=market_id,
                date=d_str,
                session_status=status,
                timezone="UTC" if "CRYPTO" in market_id else "Europe/Istanbul",
                warnings=warnings
            ))
            curr += timedelta(days=1)
        return days

    def calendar_day(self, market_id: str, date: str) -> MarketCalendarDay:
        days = self.default_calendar(market_id, date, date)
        return days[0] if days else MarketCalendarDay(
            day_id=f"{market_id}_{date}", market_id=market_id, date=date,
            session_status=MarketSessionStatus.UNKNOWN, timezone="UTC"
        )

    def is_business_day(self, market_id: str, date: str) -> bool:
        day = self.calendar_day(market_id, date)
        return day.session_status in [MarketSessionStatus.REGULAR, MarketSessionStatus.HALF_DAY, MarketSessionStatus.PRE_MARKET, MarketSessionStatus.AFTER_HOURS]

    def session_status(self, market_id: str, date: str) -> MarketSessionStatus:
        return self.calendar_day(market_id, date).session_status

    def validate_calendar(self, days: List[MarketCalendarDay]) -> List[str]:
        warnings = []
        for d in days:
            if d.session_status == MarketSessionStatus.UNKNOWN:
                warnings.append(f"Unknown session status for {d.date}")
        return warnings
