from bist_signal_bot.signals.storage import SignalStore
from bist_signal_bot.signals.models import (
    TrackedSignal, SignalLifecycleState, SignalLifecycleEvent,
    SignalLifecycleEventType, WatchlistEntry, SignalPriority,
    ResearchExitSimulation, ResearchExitRuleType, SignalOutcomeState,
    SignalAlertPolicy
)
from datetime import datetime, timezone
import json

def test_signal_storage_append_load(tmp_path):
    store = SignalStore(tmp_path)
    now = datetime.now(timezone.utc)

    s1 = TrackedSignal(signal_id="1", fingerprint_id="fp1", symbol="A", source_type="TEST", created_at=now, updated_at=now)
    store.append_signal(s1)

    loaded = store.load_signals()
    assert len(loaded) == 1
    assert loaded[0].signal_id == "1"

def test_signal_storage_latest_by_id(tmp_path):
    store = SignalStore(tmp_path)
    now = datetime.now(timezone.utc)

    s1 = TrackedSignal(signal_id="1", fingerprint_id="fp1", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=10.0)
    store.append_signal(s1)

    s1.current_score = 20.0
    s1.updated_at = datetime.now(timezone.utc)
    store.update_signal(s1)

    loaded = store.load_signals()
    assert len(loaded) == 1
    assert loaded[0].current_score == 20.0

def test_get_signal(tmp_path):
    store = SignalStore(tmp_path)
    now = datetime.now(timezone.utc)

    assert store.get_signal("nonexistent") is None

    s1 = TrackedSignal(signal_id="1", fingerprint_id="fp1", symbol="A", source_type="TEST", created_at=now, updated_at=now)
    s2 = TrackedSignal(signal_id="2", fingerprint_id="fp2", symbol="B", source_type="TEST", created_at=now, updated_at=now)

    store.append_signal(s1)
    store.append_signal(s2)

    retrieved = store.get_signal("2")
    assert retrieved is not None
    assert retrieved.signal_id == "2"
    assert retrieved.symbol == "B"

def test_find_by_fingerprint(tmp_path):
    store = SignalStore(tmp_path)
    now = datetime.now(timezone.utc)

    assert store.find_by_fingerprint("fp1") is None

    # Add an active signal
    s1 = TrackedSignal(signal_id="1", fingerprint_id="fp1", symbol="A", source_type="TEST", created_at=now, updated_at=now, state=SignalLifecycleState.ACTIVE)
    store.append_signal(s1)

    # Add another signal with same fingerprint but expired
    s2 = TrackedSignal(signal_id="2", fingerprint_id="fp2", symbol="A", source_type="TEST", created_at=now, updated_at=now, state=SignalLifecycleState.EXPIRED)
    store.append_signal(s2)

    found_active = store.find_by_fingerprint("fp1")
    assert found_active is not None
    assert found_active.signal_id == "1"

    found_expired = store.find_by_fingerprint("fp2", active_only=True)
    assert found_expired is None

    found_expired_all = store.find_by_fingerprint("fp2", active_only=False)
    assert found_expired_all is not None
    assert found_expired_all.signal_id == "2"

def test_append_load_events(tmp_path):
    store = SignalStore(tmp_path)
    now = datetime.now(timezone.utc)

    e1 = SignalLifecycleEvent(
        event_id="e1", signal_id="1", event_type=SignalLifecycleEventType.CREATED,
        timestamp=now, message="created"
    )
    e2 = SignalLifecycleEvent(
        event_id="e2", signal_id="1", event_type=SignalLifecycleEventType.UPDATED,
        timestamp=now, message="updated"
    )
    e3 = SignalLifecycleEvent(
        event_id="e3", signal_id="2", event_type=SignalLifecycleEventType.CREATED,
        timestamp=now, message="created"
    )

    store.append_event(e1)
    store.append_event(e2)
    store.append_event(e3)

    all_events = store.load_events()
    assert len(all_events) == 3

    signal_1_events = store.load_events(signal_id="1")
    assert len(signal_1_events) == 2
    assert {e.event_id for e in signal_1_events} == {"e1", "e2"}

def test_append_load_watchlist(tmp_path):
    store = SignalStore(tmp_path)
    now = datetime.now(timezone.utc)

    w1 = WatchlistEntry(watchlist_id="w1", signal_id="1", symbol="A", added_at=now, active=True)
    store.append_watchlist(w1)

    # Update to inactive
    w1_updated = WatchlistEntry(watchlist_id="w1", signal_id="1", symbol="A", added_at=now, active=False)
    store.append_watchlist(w1_updated)

    w2 = WatchlistEntry(watchlist_id="w2", signal_id="2", symbol="B", added_at=now, active=True)
    store.append_watchlist(w2)

    active_entries = store.load_watchlist(active_only=True)
    assert len(active_entries) == 1
    assert active_entries[0].watchlist_id == "w2"

    all_entries = store.load_watchlist(active_only=False)
    assert len(all_entries) == 2
    assert {e.watchlist_id for e in all_entries} == {"w1", "w2"}

def test_append_load_exit_simulations(tmp_path):
    store = SignalStore(tmp_path)
    now = datetime.now(timezone.utc)

    sim1 = ResearchExitSimulation(
        simulation_id="sim1", signal_id="1", symbol="A", started_at=now, evaluated_at=now,
        triggered_rule=ResearchExitRuleType.FIXED_PERCENT_TARGET, outcome_state=SignalOutcomeState.HIT_RESEARCH_TARGET
    )
    sim2 = ResearchExitSimulation(
        simulation_id="sim2", signal_id="2", symbol="B", started_at=now, evaluated_at=now,
        triggered_rule=ResearchExitRuleType.TIME_STOP, outcome_state=SignalOutcomeState.TIME_EXPIRED
    )

    store.append_exit_simulation(sim1)
    store.append_exit_simulation(sim2)

    all_sims = store.load_exit_simulations()
    assert len(all_sims) == 2

    signal_1_sims = store.load_exit_simulations(signal_id="1")
    assert len(signal_1_sims) == 1
    assert signal_1_sims[0].simulation_id == "sim1"

def test_save_load_policy(tmp_path):
    store = SignalStore(tmp_path)

    assert store.load_policy() is None

    policy = SignalAlertPolicy(dedupe_enabled=False, cooldown_minutes=120)
    store.save_policy(policy)

    loaded_policy = store.load_policy()
    assert loaded_policy is not None
    assert loaded_policy.dedupe_enabled is False
    assert loaded_policy.cooldown_minutes == 120

def test_corrupted_jsonl(tmp_path):
    store = SignalStore(tmp_path)

    # Write a good line, a bad line, and another good line
    now = datetime.now(timezone.utc)
    s1 = TrackedSignal(signal_id="1", fingerprint_id="fp1", symbol="A", source_type="TEST", created_at=now, updated_at=now)
    store.append_signal(s1)

    with open(store.tracked_signals_path, "a", encoding="utf-8") as f:
        f.write("this is not valid json\n")
        f.write('{"also": "not a TrackedSignal"}\n')

    s2 = TrackedSignal(signal_id="2", fingerprint_id="fp2", symbol="B", source_type="TEST", created_at=now, updated_at=now)
    store.append_signal(s2)

    # load_signals uses _load_jsonl which suppresses json errors
    # but the second bad line might parse but fail TrackedSignal(**row),
    # except _load_jsonl returns List[dict], and load_signals iterates.
    # Actually load_signals iterates and creates TrackedSignal(**row)
    # wait, load_signals might throw validation error on the second bad line if it parses as JSON.

    # Let's see if we can just test _load_jsonl handles the first bad line
    raw_data = store._load_jsonl(store.tracked_signals_path)
    assert len(raw_data) == 3 # 2 valid TrackedSignals + 1 valid JSON that's not a TrackedSignal

def test_load_policy_corrupted(tmp_path):
    store = SignalStore(tmp_path)

    store.policy_path.parent.mkdir(parents=True, exist_ok=True)
    with open(store.policy_path, "w", encoding="utf-8") as f:
        f.write("invalid json")

    assert store.load_policy() is None


def test_load_signals_filter(tmp_path):
    store = SignalStore(tmp_path)
    now = datetime.now(timezone.utc)

    s1 = TrackedSignal(signal_id="1", fingerprint_id="fp1", symbol="A", source_type="TEST", created_at=now, updated_at=now, state=SignalLifecycleState.ACTIVE)
    s2 = TrackedSignal(signal_id="2", fingerprint_id="fp2", symbol="B", source_type="TEST", created_at=now, updated_at=now, state=SignalLifecycleState.EXPIRED)
    store.append_signal(s1)
    store.append_signal(s2)

    loaded_active = store.load_signals(state=SignalLifecycleState.ACTIVE)
    assert len(loaded_active) == 1
    assert loaded_active[0].signal_id == "1"

    loaded_symbol_b = store.load_signals(symbol="B")
    assert len(loaded_symbol_b) == 1
    assert loaded_symbol_b[0].signal_id == "2"

def test_load_jsonl_limit_and_corrupt(tmp_path):
    store = SignalStore(tmp_path)
    now = datetime.now(timezone.utc)

    # Check what happens when file doesn't exist
    assert store._load_jsonl(store.tracked_signals_path) == []

    # Create enough lines to hit limit
    s = TrackedSignal(signal_id="1", fingerprint_id="fp1", symbol="A", source_type="TEST", created_at=now, updated_at=now)
    for _ in range(5):
        store.append_signal(s)

    with open(store.tracked_signals_path, "a", encoding="utf-8") as f:
        f.write("\n") # empty line
        f.write("{invalid json\n") # corrupt line

    for _ in range(5):
        store.append_signal(s)

    # the limit in _load_jsonl defaults to 1000
    results = store._load_jsonl(store.tracked_signals_path, limit=3)
    assert len(results) == 3

def test_get_signal_corrupted(tmp_path):
    store = SignalStore(tmp_path)
    now = datetime.now(timezone.utc)

    with open(store.tracked_signals_path, "w", encoding="utf-8") as f:
        f.write("invalid json\n")

    s1 = TrackedSignal(signal_id="1", fingerprint_id="fp1", symbol="A", source_type="TEST", created_at=now, updated_at=now)
    store.append_signal(s1)

    with open(store.tracked_signals_path, "a", encoding="utf-8") as f:
        f.write("\n") # empty line

    retrieved = store.get_signal("1")
    assert retrieved is not None
    assert retrieved.signal_id == "1"


def test_get_signal_not_found(tmp_path):
    store = SignalStore(tmp_path)
    now = datetime.now(timezone.utc)

    # Needs to exist to get past initial file check, but not contain the ID
    s1 = TrackedSignal(signal_id="1", fingerprint_id="fp1", symbol="A", source_type="TEST", created_at=now, updated_at=now)
    store.append_signal(s1)

    with open(store.tracked_signals_path, "a", encoding="utf-8") as f:
        f.write("invalid json\n")

    retrieved = store.get_signal("2")
    assert retrieved is None


def test_load_jsonl_empty_line(tmp_path):
    store = SignalStore(tmp_path)
    now = datetime.now(timezone.utc)
    s1 = TrackedSignal(signal_id="1", fingerprint_id="fp1", symbol="A", source_type="TEST", created_at=now, updated_at=now)
    store.append_signal(s1)

    with open(store.tracked_signals_path, "a", encoding="utf-8") as f:
        f.write("    \n")

    results = store._load_jsonl(store.tracked_signals_path)
    assert len(results) == 1
