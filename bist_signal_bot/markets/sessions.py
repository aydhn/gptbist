from datetime import datetime
from typing import List, Optional
from bist_signal_bot.markets.models import MarketSession, MarketSessionStatus

class MarketSessionProvider:
    def __init__(self, calendar_provider=None, store=None):
        self.calendar_provider = calendar_provider
        self.store = store

    def default_sessions(self, market_id: str, date: str) -> List[MarketSession]:
        status = MarketSessionStatus.REGULAR
        if self.calendar_provider:
            status = self.calendar_provider.session_status(market_id, date)

        return [
            MarketSession(
                session_id=f"{market_id}_{date}_REGULAR",
                market_id=market_id,
                date=date,
                status=status,
                session_name="REGULAR",
                timezone="UTC" if "CRYPTO" in market_id else "Europe/Istanbul"
            )
        ]

    def regular_session(self, market_id: str, date: str) -> MarketSession:
        sessions = self.default_sessions(market_id, date)
        for s in sessions:
            if s.session_name == "REGULAR":
                return s
        return sessions[0]

    def session_for_datetime(self, market_id: str, dt: datetime) -> Optional[MarketSession]:
        d_str = dt.strftime("%Y-%m-%d")
        sessions = self.default_sessions(market_id, d_str)
        return sessions[0] if sessions else None

    def validate_session(self, session: MarketSession) -> List[str]:
        warnings = []
        if not session.session_name:
            warnings.append("Session name empty")
        return warnings
