from typing import List, Optional
from datetime import datetime
import logging
from bist_signal_bot.instruments.models import SymbolLifecycleEvent, InstrumentStatus, InstrumentRecord, SymbolLifecycleEventType

logger = logging.getLogger(__name__)

class SymbolLifecycleManager:
    def __init__(self):
        self._events: List[SymbolLifecycleEvent] = []

    def add_event(self, event: SymbolLifecycleEvent, confirm: bool = False) -> SymbolLifecycleEvent:
        self._events.append(event)
        return event

    def events_for_symbol(self, symbol: str) -> List[SymbolLifecycleEvent]:
        target = symbol.upper()
        return [e for e in self._events if e.symbol.upper() == target]

    def status_as_of(self, symbol: str, as_of: datetime) -> InstrumentStatus:
        events = self.events_for_symbol(symbol)
        # Filter and sort
        past_events = sorted([e for e in events if e.effective_date <= as_of], key=lambda x: x.effective_date)

        if not past_events:
            return InstrumentStatus.UNKNOWN

        last_event = past_events[-1]
        if last_event.event_type == SymbolLifecycleEventType.LISTED:
            return InstrumentStatus.ACTIVE
        elif last_event.event_type == SymbolLifecycleEventType.DELISTED:
            return InstrumentStatus.DELISTED
        elif last_event.event_type == SymbolLifecycleEventType.SUSPENDED:
            return InstrumentStatus.SUSPENDED
        elif last_event.event_type == SymbolLifecycleEventType.RESUMED:
            return InstrumentStatus.ACTIVE

        return InstrumentStatus.UNKNOWN

    def symbol_as_of(self, symbol: str, as_of: datetime) -> Optional[str]:
        # Simple implementation
        return symbol.upper()

    def apply_lifecycle_to_master(self, events: List[SymbolLifecycleEvent], confirm: bool = False) -> List[InstrumentRecord]:
        if not confirm:
            logger.warning("apply_lifecycle_to_master requires confirm=True")
            return []
        return []
