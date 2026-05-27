from datetime import datetime, timedelta
from typing import Any
import uuid

from bist_signal_bot.events.models import (
    MarketEvent,
    MarketEventType,
    EventCalendarSnapshot
)

class EventCalendar:
    def __init__(self, store=None):
        self.store = store
        self._events: dict[str, MarketEvent] = {}
        if self.store:
            for ev in self.store.load_events():
                self._events[ev.event_id] = ev

    def add_event(self, event: MarketEvent, confirm: bool = False) -> MarketEvent:
        if event.symbol:
            event.symbol = event.symbol.upper()

        for existing in self._events.values():
            if (existing.symbol == event.symbol and
                existing.event_type == event.event_type and
                existing.event_date.date() == event.event_date.date() and
                existing.title == event.title):
                # Duplicate found
                return existing

        self._events[event.event_id] = event
        if confirm and self.store:
            self.store.append_event(event)
        return event

    def get_event(self, event_id: str) -> MarketEvent | None:
        return self._events.get(event_id)

    def list_events(self, symbol: str | None = None, sector: str | None = None, event_type: MarketEventType | None = None, start: datetime | None = None, end: datetime | None = None, include_cancelled: bool = False, limit: int = 1000) -> list[MarketEvent]:
        results = []
        for ev in self._events.values():
            if symbol and ev.symbol != symbol.upper():
                continue
            if sector and ev.sector != sector:
                continue
            if event_type and ev.event_type != event_type:
                continue
            if start and ev.event_date < start:
                continue
            if end and ev.event_date > end:
                continue
            if not include_cancelled and ev.status == "CANCELLED":
                continue
            results.append(ev)

        results.sort(key=lambda x: x.event_date)
        return results[:limit]

    def upcoming_events(self, days: int = 30, symbol: str | None = None) -> list[MarketEvent]:
        now = datetime.now()
        end = now + timedelta(days=days)
        return self.list_events(symbol=symbol, start=now, end=end)

    def events_for_symbol(self, symbol: str, as_of: datetime | None = None, lookback_days: int = 5, lookahead_days: int = 10) -> list[MarketEvent]:
        as_of = as_of or datetime.now()
        start = as_of - timedelta(days=lookback_days)
        end = as_of + timedelta(days=lookahead_days)
        return self.list_events(symbol=symbol, start=start, end=end)

    def events_for_portfolio(self, symbols: list[str], as_of: datetime | None = None, lookback_days: int = 5, lookahead_days: int = 10) -> list[MarketEvent]:
        results = []
        for symbol in symbols:
            results.extend(self.events_for_symbol(symbol, as_of, lookback_days, lookahead_days))

        # Add market-wide events
        as_of = as_of or datetime.now()
        start = as_of - timedelta(days=lookback_days)
        end = as_of + timedelta(days=lookahead_days)
        market_events = [ev for ev in self.list_events(start=start, end=end) if ev.scope in ["MARKET", "MACRO"]]
        results.extend(market_events)

        # Deduplicate
        unique_results = {ev.event_id: ev for ev in results}
        return list(unique_results.values())

    def snapshot(self) -> EventCalendarSnapshot:
        now = datetime.now()
        upcoming = self.upcoming_events()

        symbols = set()
        sectors = set()
        type_counts = {}
        high_severity = 0

        for ev in self._events.values():
            if ev.symbol:
                symbols.add(ev.symbol)
            if ev.sector:
                sectors.add(ev.sector)

            type_counts[ev.event_type] = type_counts.get(ev.event_type, 0) + 1

            if ev.severity in ["HIGH", "CRITICAL"]:
                high_severity += 1

        return EventCalendarSnapshot(
            snapshot_id=str(uuid.uuid4()),
            created_at=now,
            events_count=len(self._events),
            upcoming_count=len(upcoming),
            high_severity_count=high_severity,
            symbols_with_events=list(symbols),
            sectors_with_events=list(sectors),
            event_type_counts=type_counts
        )

# Added for Disclosure Integration
# DisclosureEventExtraction can be mapped to MarketEvent with user confirmation
