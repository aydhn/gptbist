from datetime import datetime, timezone, timedelta
from bist_signal_bot.signals.deduplication import SignalDeduplicator
from bist_signal_bot.signals.models import TrackedSignal, SignalAlertPolicy, SignalAlertDecision, SignalPriority

def test_dedupe_new_signal():
    deduper = SignalDeduplicator()
    policy = SignalAlertPolicy()

    current = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=datetime.now(), updated_at=datetime.now())
    res = deduper.evaluate_alert(current, None, policy)
    assert res.decision == SignalAlertDecision.SEND
    assert res.should_send is True
    assert res.should_add_to_digest is True

def test_dedupe_cooldown():
    deduper = SignalDeduplicator()
    policy = SignalAlertPolicy(cooldown_minutes=60)
    now = datetime.now(timezone.utc)

    prev = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now)
    prev.last_alert_at = now - timedelta(minutes=30)

    current = TrackedSignal(signal_id="2", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now)

    res = deduper.evaluate_alert(current, prev, policy, now=now)
    assert res.decision == SignalAlertDecision.MUTE_COOLDOWN
    assert res.should_send is False
    assert res.should_add_to_digest is True

def test_dedupe_unchanged():
    deduper = SignalDeduplicator()
    policy = SignalAlertPolicy(cooldown_minutes=60, min_score_change_for_repeat_alert=5.0)
    now = datetime.now(timezone.utc)

    prev = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=80.0)
    prev.last_alert_at = now - timedelta(minutes=61)

    current = TrackedSignal(signal_id="2", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=82.0)

    res = deduper.evaluate_alert(current, prev, policy, now=now)
    assert res.decision == SignalAlertDecision.MUTE_UNCHANGED
    assert res.should_send is False
    assert res.should_add_to_digest is False

def test_dedupe_cooldown_override_critical():
    deduper = SignalDeduplicator()
    policy = SignalAlertPolicy(cooldown_minutes=60, allow_critical_repeat=True, min_score_change_for_repeat_alert=5.0)
    now = datetime.now(timezone.utc)

    prev = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=80.0, priority=SignalPriority.CRITICAL)
    prev.last_alert_at = now - timedelta(minutes=30)

    # Score changed enough, critical priority
    current = TrackedSignal(signal_id="2", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=86.0, priority=SignalPriority.CRITICAL)

    res = deduper.evaluate_alert(current, prev, policy, now=now)
    assert res.decision == SignalAlertDecision.SEND
    assert res.should_send is True

def test_dedupe_max_alerts_reached_dedupe_enabled():
    deduper = SignalDeduplicator()
    policy = SignalAlertPolicy(cooldown_minutes=60, min_score_change_for_repeat_alert=5.0, max_alerts_per_signal=3, dedupe_enabled=True)
    now = datetime.now(timezone.utc)

    prev = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=80.0, alert_count=3)
    prev.last_alert_at = now - timedelta(minutes=61)

    current = TrackedSignal(signal_id="2", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=86.0)

    res = deduper.evaluate_alert(current, prev, policy, now=now)
    assert res.decision == SignalAlertDecision.MUTE_DUPLICATE
    assert res.should_send is False

def test_dedupe_max_alerts_reached_dedupe_disabled():
    deduper = SignalDeduplicator()
    policy = SignalAlertPolicy(cooldown_minutes=60, min_score_change_for_repeat_alert=5.0, max_alerts_per_signal=3, dedupe_enabled=False)
    now = datetime.now(timezone.utc)

    prev = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=80.0, alert_count=3)
    prev.last_alert_at = now - timedelta(minutes=61)

    current = TrackedSignal(signal_id="2", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=86.0)

    res = deduper.evaluate_alert(current, prev, policy, now=now)
    assert res.decision == SignalAlertDecision.SEND_DIGEST_ONLY
    assert res.should_send is True
    assert res.should_add_to_digest is True

def test_dedupe_high_conflict_mute():
    deduper = SignalDeduplicator()
    policy = SignalAlertPolicy(mute_high_conflict=True)
    now = datetime.now(timezone.utc)

    current = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, risk_decision="HIGH_CONFLICT")

    res = deduper.evaluate_alert(current, None, policy, now=now)
    assert res.decision == SignalAlertDecision.MUTE_HIGH_CONFLICT
    assert res.should_send is False

def test_dedupe_low_priority():
    deduper = SignalDeduplicator()
    policy = SignalAlertPolicy(digest_only_below_priority=SignalPriority.HIGH)
    now = datetime.now(timezone.utc)

    current = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, priority=SignalPriority.NORMAL)

    res = deduper.evaluate_alert(current, None, policy, now=now)
    assert res.decision == SignalAlertDecision.SEND_DIGEST_ONLY
    assert res.should_send is True

def test_score_changed_enough():
    deduper = SignalDeduplicator()
    now = datetime.now(timezone.utc)
    prev = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=80.0)
    current = TrackedSignal(signal_id="2", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=85.0)

    assert deduper.score_changed_enough(prev, current, 5.0) is True
    assert deduper.score_changed_enough(prev, current, 5.1) is False

def test_merge_duplicate_signals():
    deduper = SignalDeduplicator()
    now = datetime.now(timezone.utc)

    s1 = TrackedSignal(signal_id="1", fingerprint_id="fp1", symbol="A", source_type="TEST", created_at=now, updated_at=now - timedelta(minutes=5))
    s2 = TrackedSignal(signal_id="2", fingerprint_id="fp1", symbol="A", source_type="TEST", created_at=now, updated_at=now)
    s3 = TrackedSignal(signal_id="3", fingerprint_id="fp2", symbol="B", source_type="TEST", created_at=now, updated_at=now)

    merged = deduper.merge_duplicate_signals([s1, s2, s3])
    assert len(merged) == 2
    assert any(s.signal_id == "2" for s in merged)
    assert any(s.signal_id == "3" for s in merged)
    assert not any(s.signal_id == "1" for s in merged)

def test_evaluate_alert_now_is_none():
    deduper = SignalDeduplicator()
    policy = SignalAlertPolicy()
    current = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=datetime.now(), updated_at=datetime.now())

    # Passing now=None explicitly to hit the branch `if now is None:`
    res = deduper.evaluate_alert(current, None, policy, now=None)
    assert res.decision == SignalAlertDecision.SEND

def test_priority_too_low():
    deduper = SignalDeduplicator()

    # Testing threshold combinations
    assert deduper._priority_too_low(SignalPriority.LOW, SignalPriority.NORMAL) is True
    assert deduper._priority_too_low(SignalPriority.NORMAL, SignalPriority.NORMAL) is False
    assert deduper._priority_too_low(SignalPriority.HIGH, SignalPriority.NORMAL) is False

    # UNKNOWN handling
    assert deduper._priority_too_low(SignalPriority.UNKNOWN, SignalPriority.NORMAL) is True

def test_cooldown_remaining():
    deduper = SignalDeduplicator()
    now = datetime.now(timezone.utc)

    # No previous alert
    prev_no_alert = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now)
    assert deduper.cooldown_remaining(prev_no_alert, 60, now) == 0.0

    # With previous alert
    prev_with_alert = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now)
    prev_with_alert.last_alert_at = now - timedelta(minutes=30)

    rem = deduper.cooldown_remaining(prev_with_alert, 60, now)
    assert 29.0 <= rem <= 31.0

    # Cooldown expired
    prev_expired = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now)
    prev_expired.last_alert_at = now - timedelta(minutes=90)

    assert deduper.cooldown_remaining(prev_expired, 60, now) == 0.0

def test_dedupe_cooldown_override_critical_not_enough_change():
    deduper = SignalDeduplicator()
    policy = SignalAlertPolicy(cooldown_minutes=60, allow_critical_repeat=True, min_score_change_for_repeat_alert=5.0)
    now = datetime.now(timezone.utc)

    prev = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=80.0, priority=SignalPriority.CRITICAL)
    prev.last_alert_at = now - timedelta(minutes=30)

    # Score didn't change enough
    current = TrackedSignal(signal_id="2", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=81.0, priority=SignalPriority.CRITICAL)

    res = deduper.evaluate_alert(current, prev, policy, now=now)
    # Should still be in cooldown because score change is insufficient
    assert res.decision == SignalAlertDecision.MUTE_COOLDOWN

def test_dedupe_cooldown_expired_and_score_changed():
    deduper = SignalDeduplicator()
    policy = SignalAlertPolicy(cooldown_minutes=60, min_score_change_for_repeat_alert=5.0)
    now = datetime.now(timezone.utc)

    prev = TrackedSignal(signal_id="1", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=80.0)
    prev.last_alert_at = now - timedelta(minutes=61)

    current = TrackedSignal(signal_id="2", fingerprint_id="fp", symbol="A", source_type="TEST", created_at=now, updated_at=now, current_score=86.0)

    res = deduper.evaluate_alert(current, prev, policy, now=now)
    assert res.decision == SignalAlertDecision.SEND
    assert res.should_send is True
