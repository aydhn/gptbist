from datetime import datetime, timezone, timedelta
from bist_signal_bot.signals.deduplication import SignalDeduplicator
from bist_signal_bot.signals.models import TrackedSignal, SignalAlertPolicy, SignalAlertDecision

def test_dedupe_new_signal():
    deduper = SignalDeduplicator()
    policy = SignalAlertPolicy()

    current = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=datetime.now(), updated_at=datetime.now())
    res = deduper.evaluate_alert(current, None, policy)
    assert res.decision == SignalAlertDecision.SEND

def test_dedupe_cooldown():
    deduper = SignalDeduplicator()
    policy = SignalAlertPolicy(cooldown_minutes=60)
    now = datetime.now(timezone.utc)

    prev = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now)
    prev.last_alert_at = now - timedelta(minutes=30)

    current = TrackedSignal(signal_id="2", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now)

    res = deduper.evaluate_alert(current, prev, policy, now=now)
    assert res.decision == SignalAlertDecision.MUTE_COOLDOWN

def test_dedupe_unchanged():
    deduper = SignalDeduplicator()
    policy = SignalAlertPolicy(cooldown_minutes=60, min_score_change_for_repeat_alert=5.0)
    now = datetime.now(timezone.utc)

    prev = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=80.0)
    prev.last_alert_at = now - timedelta(minutes=61)

    current = TrackedSignal(signal_id="2", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=82.0)

    res = deduper.evaluate_alert(current, prev, policy, now=now)
    assert res.decision == SignalAlertDecision.MUTE_UNCHANGED
