import pytest
from datetime import datetime
from bist_signal_bot.instruments.models import SymbolLifecycleEvent, SymbolLifecycleEventType, InstrumentStatus
from bist_signal_bot.instruments.lifecycle import SymbolLifecycleManager

def test_symbol_lifecycle_add():
    mgr = SymbolLifecycleManager()
    ev = SymbolLifecycleEvent(
        event_id="e1",
        symbol="XYZ",
        event_type=SymbolLifecycleEventType.LISTED,
        effective_date=datetime(2020, 1, 1),
        source="test"
    )
    mgr.add_event(ev)
    assert mgr.status_as_of("XYZ", datetime(2021, 1, 1)) == InstrumentStatus.ACTIVE
