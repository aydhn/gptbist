import pytest
from bist_signal_bot.events.storage import EventStore
from bist_signal_bot.events.models import MarketEvent, MarketEventType, MarketEventScope, MarketEventStatus, EventSeverity
from datetime import datetime

def test_event_store_append_load(tmp_path):
    store = EventStore(tmp_path)

    event = MarketEvent(
        event_id="e1",
        event_type=MarketEventType.EARNINGS,
        scope=MarketEventScope.SYMBOL,
        status=MarketEventStatus.CONFIRMED,
        title="Earnings",
        symbol="ASELS",
        event_date=datetime.now(),
        severity=EventSeverity.HIGH,
        source="test"
    )

    store.append_event(event)
    events = store.load_events()

    assert len(events) == 1
    assert events[0].event_id == "e1"
