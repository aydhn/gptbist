import pytest
from pathlib import Path
from datetime import datetime, timezone
from bist_signal_bot.signals.models import (
    TrackedSignal, SignalLifecycleEvent, WatchlistEntry,
    ResearchExitSimulation, SignalAlertPolicy, SignalLifecycleState,
    SignalLifecycleEventType, SignalOutcomeState, ResearchExitRuleType
)
from bist_signal_bot.signals.storage import SignalStore

@pytest.fixture
def store(tmp_path):
    return SignalStore(base_dir=tmp_path)

def create_mock_signal(signal_id="sig1", fingerprint_id="fp1", symbol="AAPL", state=SignalLifecycleState.NEW) -> TrackedSignal:
    return TrackedSignal(
        signal_id=signal_id,
        fingerprint_id=fingerprint_id,
        symbol=symbol,
        source_type="TEST",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        state=state
    )

def test_append_and_load_signals(store):
    sig1 = create_mock_signal(signal_id="s1")
    sig2 = create_mock_signal(signal_id="s2", symbol="MSFT", state=SignalLifecycleState.ACTIVE)

    store.append_signal(sig1)
    store.append_signal(sig2)

    signals = store.load_signals()
    assert len(signals) == 2
    assert {s.signal_id for s in signals} == {"s1", "s2"}

    # Test filters
    filtered = store.load_signals(state=SignalLifecycleState.ACTIVE)
    assert len(filtered) == 1
    assert filtered[0].signal_id == "s2"

    filtered_sym = store.load_signals(symbol="AAPL")
    assert len(filtered_sym) == 1
    assert filtered_sym[0].signal_id == "s1"

def test_update_signal_overwrites_latest(store):
    sig1 = create_mock_signal(signal_id="s1")
    store.append_signal(sig1)

    # Update it
    sig1.state = SignalLifecycleState.ACTIVE
    sig1.updated_at = datetime.now(timezone.utc)
    store.update_signal(sig1)

    signals = store.load_signals()
    assert len(signals) == 1
    assert signals[0].state == SignalLifecycleState.ACTIVE

def test_get_signal(store):
    sig1 = create_mock_signal(signal_id="s1")
    sig2 = create_mock_signal(signal_id="s2")
    store.append_signal(sig1)
    store.append_signal(sig2)

    fetched = store.get_signal("s1")
    assert fetched is not None
    assert fetched.signal_id == "s1"

    assert store.get_signal("nonexistent") is None

def test_find_by_fingerprint(store):
    sig1 = create_mock_signal(signal_id="s1", fingerprint_id="fp1", state=SignalLifecycleState.NEW)
    store.append_signal(sig1)

    # active_only=True
    fetched = store.find_by_fingerprint("fp1", active_only=True)
    assert fetched is not None
    assert fetched.signal_id == "s1"

    # Update state to inactive
    sig1.state = SignalLifecycleState.COMPLETED
    sig1.updated_at = datetime.now(timezone.utc)
    store.update_signal(sig1)

    # active_only=True should return None now
    assert store.find_by_fingerprint("fp1", active_only=True) is None

    # active_only=False should return it
    fetched = store.find_by_fingerprint("fp1", active_only=False)
    assert fetched is not None
    assert fetched.state == SignalLifecycleState.COMPLETED

def test_events(store):
    event1 = SignalLifecycleEvent(
        event_id="e1",
        signal_id="s1",
        event_type=SignalLifecycleEventType.CREATED,
        timestamp=datetime.now(timezone.utc),
        message="Test event 1"
    )
    event2 = SignalLifecycleEvent(
        event_id="e2",
        signal_id="s1",
        event_type=SignalLifecycleEventType.UPDATED,
        timestamp=datetime.now(timezone.utc),
        message="Test event 2"
    )
    event3 = SignalLifecycleEvent(
        event_id="e3",
        signal_id="s2",
        event_type=SignalLifecycleEventType.CREATED,
        timestamp=datetime.now(timezone.utc),
        message="Test event 3"
    )

    store.append_event(event1)
    store.append_event(event2)
    store.append_event(event3)

    all_events = store.load_events()
    assert len(all_events) == 3

    s1_events = store.load_events(signal_id="s1")
    assert len(s1_events) == 2
    assert {e.event_id for e in s1_events} == {"e1", "e2"}

def test_watchlist(store):
    w1 = WatchlistEntry(
        watchlist_id="w1",
        signal_id="s1",
        symbol="AAPL",
        added_at=datetime.now(timezone.utc),
        active=True
    )
    store.append_watchlist(w1)

    wlist = store.load_watchlist()
    assert len(wlist) == 1
    assert wlist[0].watchlist_id == "w1"

    # Update to inactive
    w1.active = False
    store.append_watchlist(w1)

    assert len(store.load_watchlist(active_only=True)) == 0
    assert len(store.load_watchlist(active_only=False)) == 1

def test_exit_simulations(store):
    sim1 = ResearchExitSimulation(
        simulation_id="sim1",
        signal_id="s1",
        symbol="AAPL",
        started_at=datetime.now(timezone.utc),
        evaluated_at=datetime.now(timezone.utc),
        triggered_rule=ResearchExitRuleType.FIXED_PERCENT_TARGET,
        outcome_state=SignalOutcomeState.HIT_RESEARCH_TARGET
    )
    store.append_exit_simulation(sim1)

    sims = store.load_exit_simulations()
    assert len(sims) == 1
    assert sims[0].simulation_id == "sim1"

    assert len(store.load_exit_simulations(signal_id="s1")) == 1
    assert len(store.load_exit_simulations(signal_id="s2")) == 0

def test_policy(store):
    policy = SignalAlertPolicy(
        dedupe_enabled=False,
        cooldown_minutes=120
    )

    # Before saving
    assert store.load_policy() is None

    store.save_policy(policy)

    loaded = store.load_policy()
    assert loaded is not None
    assert loaded.dedupe_enabled is False
    assert loaded.cooldown_minutes == 120

def test_corrupted_jsonl(store):
    # Manually write corrupted data
    store.tracked_signals_path.parent.mkdir(parents=True, exist_ok=True)
    with open(store.tracked_signals_path, "w") as f:
        f.write('{"signal_id": "valid1", "fingerprint_id": "fp1", "symbol": "AAPL", "source_type": "T", "created_at": "2023-01-01T00:00:00Z", "updated_at": "2023-01-01T00:00:00Z", "state": "NEW", "priority": "NORMAL", "outcome_state": "NOT_TRACKED"}\n')
        f.write('not valid json\n')
        f.write('{"signal_id": "valid2", "fingerprint_id": "fp2", "symbol": "MSFT", "source_type": "T", "created_at": "2023-01-01T00:00:00Z", "updated_at": "2023-01-01T00:00:00Z", "state": "NEW", "priority": "NORMAL", "outcome_state": "NOT_TRACKED"}\n')

    signals = store.load_signals()
    assert len(signals) == 2
    assert {s.signal_id for s in signals} == {"valid1", "valid2"}

    # test get_signal on corrupted data
    assert store.get_signal("valid1").signal_id == "valid1"
    assert store.get_signal("valid2").signal_id == "valid2"

def test_corrupted_policy_json(store):
    store.policy_path.parent.mkdir(parents=True, exist_ok=True)
    store.policy_path.write_text("not valid json")

    # Should handle error gracefully and return None
    assert store.load_policy() is None


def test_missing_files(store):
    assert store._load_jsonl(store.tracked_signals_path) == []
    assert store.get_signal("s1") is None
    assert store.find_by_fingerprint("fp1") is None

def test_load_jsonl_limit(store):
    store.tracked_signals_path.parent.mkdir(parents=True, exist_ok=True)
    with open(store.tracked_signals_path, "w") as f:
        for i in range(5):
            f.write(f'{{"signal_id": "valid{i}", "fingerprint_id": "fp{i}", "symbol": "AAPL", "source_type": "T", "created_at": "2023-01-01T00:00:00Z", "updated_at": "2023-01-01T00:00:00Z", "state": "NEW", "priority": "NORMAL", "outcome_state": "NOT_TRACKED"}}\n')

    # load_signals uses _load_jsonl(path, limit=limit*10)
    # The default limit for _load_jsonl is what we're testing directly.
    assert len(store._load_jsonl(store.tracked_signals_path, limit=2)) == 2
    assert len(store._load_jsonl(store.tracked_signals_path, limit=10)) == 5

def test_empty_lines(store):
    store.tracked_signals_path.parent.mkdir(parents=True, exist_ok=True)
    with open(store.tracked_signals_path, "w") as f:
        f.write('{"signal_id": "valid1", "fingerprint_id": "fp1", "symbol": "AAPL", "source_type": "T", "created_at": "2023-01-01T00:00:00Z", "updated_at": "2023-01-01T00:00:00Z", "state": "NEW", "priority": "NORMAL", "outcome_state": "NOT_TRACKED"}\n')
        f.write('\n')
        f.write('   \n')
        f.write('{"signal_id": "valid2", "fingerprint_id": "fp2", "symbol": "AAPL", "source_type": "T", "created_at": "2023-01-01T00:00:00Z", "updated_at": "2023-01-01T00:00:00Z", "state": "NEW", "priority": "NORMAL", "outcome_state": "NOT_TRACKED"}\n')

    signals = store.load_signals()
    assert len(signals) == 2

    sig = store.get_signal("valid1")
    assert sig is not None
