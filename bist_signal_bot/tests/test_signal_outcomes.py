from bist_signal_bot.signals.outcomes import SignalOutcomeTracker
from bist_signal_bot.signals.models import TrackedSignal, SignalOutcomeState
from bist_signal_bot.signals.storage import SignalStore
from datetime import datetime, timezone

def test_outcome_tracker(tmp_path):
    store = SignalStore(tmp_path)
    ot = SignalOutcomeTracker(store)

    now = datetime.now(timezone.utc)
    s = TrackedSignal(signal_id="sig1", fingerprint_id="fp1", symbol="ASELS", source_type="TEST", created_at=now, updated_at=now)
    store.append_signal(s)

    ot.update_manual_outcome("sig1", SignalOutcomeState.HIT_RESEARCH_TARGET, 5.0, confirm=True)

    s_updated = store.get_signal("sig1")
    assert s_updated.outcome_state == SignalOutcomeState.HIT_RESEARCH_TARGET
    assert s_updated.outcome_return_pct == 5.0

    summary = ot.summarize_outcomes()
    assert summary["target_hits"] == 1
    assert summary["average_simulated_return"] == 5.0
