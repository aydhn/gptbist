import pytest
from datetime import datetime, timedelta
from pathlib import Path

from bist_signal_bot.events.models import MarketEvent, MarketEventType, MarketEventScope, MarketEventStatus, EventSeverity
from bist_signal_bot.events.calendar import EventCalendar
from bist_signal_bot.events.storage import EventStore
from bist_signal_bot.events.importer import EventImporter
from bist_signal_bot.events.windows import EventWindowBuilder
from bist_signal_bot.events.risk import EventRiskEngine
from bist_signal_bot.events.blackout import BlackoutPolicyManager

@pytest.fixture
def tmp_store(tmp_path):
    return EventStore(base_dir=tmp_path)

@pytest.fixture
def dummy_event():
    return MarketEvent(
        event_id="test-1",
        event_type=MarketEventType.EARNINGS,
        scope=MarketEventScope.SYMBOL,
        status=MarketEventStatus.SCHEDULED,
        title="ASELS Q3 Earnings",
        symbol="ASELS",
        event_date=datetime.now(),
        severity=EventSeverity.HIGH,
        source="TEST"
    )

def test_event_calendar_add_and_list(tmp_store, dummy_event):
    calendar = EventCalendar(store=tmp_store)
    calendar.add_event(dummy_event, confirm=True)

    events = calendar.list_events()
    assert len(events) == 1
    assert events[0].symbol == "ASELS"

def test_event_calendar_duplicate_prevention(tmp_store, dummy_event):
    calendar = EventCalendar(store=tmp_store)
    calendar.add_event(dummy_event, confirm=False)
    calendar.add_event(dummy_event, confirm=False)

    events = calendar.list_events()
    assert len(events) == 1

def test_event_importer_csv(tmp_path):
    csv_file = tmp_path / "events.csv"
    csv_file.write_text(
        "event_type,scope,status,title,symbol,event_date,start_at,end_at,severity,source,confidence\n"
        "EARNINGS,SYMBOL,SCHEDULED,ASELS Earnings,ASELS,2024-05-01T00:00:00,,,HIGH,TEST,0.9\n"
        "BROKEN_ROW\n"
    )

    calendar = EventCalendar()
    importer = EventImporter(calendar=calendar)

    res = importer.import_file(csv_file, confirm=True)
    assert res.events_imported == 1
    assert len(calendar.list_events()) == 1

def test_event_window_builder(dummy_event):
    builder = EventWindowBuilder()
    windows = builder.build_windows([dummy_event])

    assert len(windows) == 1
    w = windows[0]
    assert w.window_type == "EVENT_DAY"
    assert "ASELS" in w.applies_to_symbols

def test_blackout_policy_manager(dummy_event):
    manager = BlackoutPolicyManager()
    policy = manager.get_policy("Earnings Pre/Post Window")

    assert policy is not None
    window = manager.evaluate_policy(dummy_event, policy)
    assert window is not None
    assert window.window_type == "BLACKOUT"

def test_event_risk_engine(dummy_event):
    calendar = EventCalendar()
    calendar.add_event(dummy_event)

    builder = EventWindowBuilder()
    manager = BlackoutPolicyManager()

    engine = EventRiskEngine(calendar=calendar, window_builder=builder, policy_manager=manager)
    assessment = engine.assess_symbol("ASELS", as_of=dummy_event.event_date)

    assert assessment.risk_score is not None
    assert assessment.risk_score > 0
    assert assessment.decision.value != "ALLOW"
