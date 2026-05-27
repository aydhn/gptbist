from datetime import datetime, timedelta
import uuid

from bist_signal_bot.events.models import (
    MarketEvent, MarketEventType, EventSeverity, EventWindow, EventWindowType, BlackoutPolicy, EventRiskDecision
)

class EventWindowBuilder:
    def build_windows(self, events: list[MarketEvent], policies: list[BlackoutPolicy] | None = None) -> list[EventWindow]:
        windows = []
        for ev in events:
            # We create a simple window for the event day by default
            policy = None
            if policies:
                for p in policies:
                    if ev.event_type in p.event_types and p.enabled:
                        policy = p
                        break

            windows.extend(self.window_for_event(ev, policy))

        return windows

    def window_for_event(self, event: MarketEvent, policy: BlackoutPolicy | None = None) -> list[EventWindow]:
        windows = []

        pre_days, post_days = self.default_pre_post_days(event.event_type, event.severity)
        decision = EventRiskDecision.WARN

        if policy:
            pre_days = policy.pre_event_days
            post_days = policy.post_event_days
            decision = policy.decision

        starts_at = event.event_date - timedelta(days=pre_days)
        ends_at = event.event_date + timedelta(days=post_days)

        applies_to_symbols = []
        if event.symbol:
            applies_to_symbols.append(event.symbol)

        applies_to_sectors = []
        if event.sector:
            applies_to_sectors.append(event.sector)

        applies_to_market = event.scope in ["MARKET", "MACRO"]

        window = EventWindow(
            window_id=str(uuid.uuid4()),
            event_id=event.event_id,
            window_type=EventWindowType.BLACKOUT if policy else EventWindowType.EVENT_DAY,
            starts_at=starts_at,
            ends_at=ends_at,
            applies_to_symbols=applies_to_symbols,
            applies_to_sectors=applies_to_sectors,
            applies_to_market=applies_to_market,
            severity=event.severity,
            decision=decision,
            reason=f"Window for {event.title}"
        )
        windows.append(window)
        return windows

    def default_pre_post_days(self, event_type: MarketEventType, severity: EventSeverity) -> tuple[int, int]:
        if event_type in [MarketEventType.EARNINGS, MarketEventType.FINANCIAL_STATEMENT]:
            return 3, 2
        elif event_type in [MarketEventType.MACRO_DATA, MarketEventType.CENTRAL_BANK, MarketEventType.INTEREST_RATE_DECISION]:
            return 1, 1
        elif event_type == MarketEventType.CORPORATE_ACTION:
            return 2, 2

        if severity in [EventSeverity.HIGH, EventSeverity.CRITICAL]:
            return 2, 2

        return 0, 0

    def active_windows(self, as_of: datetime, windows: list[EventWindow], symbol: str | None = None, sector: str | None = None) -> list[EventWindow]:
        active = []
        for w in windows:
            if w.starts_at <= as_of <= w.ends_at:
                if symbol and self.window_matches_symbol(w, symbol, sector):
                    active.append(w)
                elif not symbol:
                    active.append(w)
        return active

    def window_matches_symbol(self, window: EventWindow, symbol: str, sector: str | None = None) -> bool:
        if window.applies_to_market:
            return True
        if symbol in window.applies_to_symbols:
            return True
        if sector and sector in window.applies_to_sectors:
            return True
        return False
