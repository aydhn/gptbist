import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Tuple, Optional, List
from bist_signal_bot.signals.models import (
    TrackedSignal, SignalLifecycleState, SignalLifecycleEventType, SignalLifecycleEvent,
    SignalLifecycleSummary, SignalAlertPolicy, AlertEvaluationResult, SignalFingerprint, SignalAlertDecision
)
from bist_signal_bot.signals.fingerprint import SignalFingerprintBuilder
from bist_signal_bot.signals.deduplication import SignalDeduplicator
from bist_signal_bot.signals.storage import SignalStore
from bist_signal_bot.config.settings import get_settings

logger = logging.getLogger(__name__)

class SignalLifecycleManager:
    def __init__(self, store: SignalStore, fingerprint_builder: SignalFingerprintBuilder, alert_policy: SignalAlertPolicy):
        self.store = store
        self.fingerprint_builder = fingerprint_builder
        self.alert_policy = alert_policy
        self.deduplicator = SignalDeduplicator()
        self.settings = get_settings()

    def track_signal(self, signal: Any, source_type: str, timeframe: Optional[str] = None) -> Tuple[TrackedSignal, AlertEvaluationResult]:
        now = datetime.now(timezone.utc)
        fingerprint = self.fingerprint_builder.build_from_signal(signal, source_type, timeframe)

        existing_signal = self.store.find_by_fingerprint(fingerprint.fingerprint_id, active_only=True)

        if existing_signal:
            tracked = self.update_tracked_signal(existing_signal, signal)
            self._append_event(tracked.signal_id, SignalLifecycleEventType.UPDATED, existing_signal.state, tracked.state, "Signal updated")
        else:
            tracked = self.create_tracked_signal(signal, fingerprint)
            self._append_event(tracked.signal_id, SignalLifecycleEventType.CREATED, None, tracked.state, "Signal created")

        eval_result = self.deduplicator.evaluate_alert(tracked, existing_signal, self.alert_policy, now)

        if eval_result.decision == SignalAlertDecision.MUTE_COOLDOWN:
            tracked.state = SignalLifecycleState.COOLDOWN
            self._append_event(tracked.signal_id, SignalLifecycleEventType.COOLDOWN_STARTED, existing_signal.state if existing_signal else None, tracked.state, "Cooldown started")
        elif eval_result.decision in [SignalAlertDecision.SEND, SignalAlertDecision.SEND_DIGEST_ONLY]:
            tracked.alert_count += 1
            tracked.last_alert_at = now
            tracked.state = SignalLifecycleState.ACTIVE
            self._append_event(tracked.signal_id, SignalLifecycleEventType.ALERT_SENT, existing_signal.state if existing_signal else None, tracked.state, "Alert sent")
        else:
            tracked.state = SignalLifecycleState.MUTED
            self._append_event(tracked.signal_id, SignalLifecycleEventType.ALERT_MUTED, existing_signal.state if existing_signal else None, tracked.state, f"Alert muted: {eval_result.decision}")

        # Save updated state
        tracked.updated_at = now
        self.store.update_signal(tracked)

        return tracked, eval_result

    def create_tracked_signal(self, signal: Any, fingerprint: SignalFingerprint) -> TrackedSignal:
        now = datetime.now(timezone.utc)
        from bist_signal_bot.signals.policy import SignalPolicyManager
        priority = SignalPolicyManager().priority_from_signal(signal)

        valid_until = now + timedelta(minutes=self.alert_policy.validity_minutes)

        tracked = TrackedSignal(
            signal_id=str(uuid.uuid4()),
            fingerprint_id=fingerprint.fingerprint_id,
            symbol=fingerprint.symbol,
            strategy_name=fingerprint.strategy_name,
            source_type=fingerprint.source_type,
            timeframe=fingerprint.timeframe,
            created_at=now,
            updated_at=now,
            valid_until=valid_until,
            state=SignalLifecycleState(getattr(self.settings, 'SIGNAL_LIFECYCLE_DEFAULT_STATE', 'NEW')),
            priority=priority,
            direction=fingerprint.signal_direction,
            initial_score=getattr(signal, 'score', None),
            current_score=getattr(signal, 'score', None),
            confidence=getattr(signal, 'confidence', None),
            risk_decision=getattr(signal, 'risk_decision', None),
            reasons=getattr(signal, 'reasons', []),
            warnings=getattr(signal, 'warnings', []),
            metadata=fingerprint.metadata
        )
        return tracked

    def update_tracked_signal(self, existing: TrackedSignal, signal: Any) -> TrackedSignal:
        now = datetime.now(timezone.utc)
        from bist_signal_bot.signals.policy import SignalPolicyManager
        priority = SignalPolicyManager().priority_from_signal(signal)

        existing.updated_at = now
        existing.last_seen_at = now
        existing.current_score = getattr(signal, 'score', existing.current_score)
        existing.confidence = getattr(signal, 'confidence', existing.confidence)
        existing.risk_decision = getattr(signal, 'risk_decision', existing.risk_decision)
        existing.priority = priority
        existing.valid_until = now + timedelta(minutes=self.alert_policy.validity_minutes)
        return existing

    def _append_event(self, signal_id: str, event_type: SignalLifecycleEventType, prev_state: Optional[SignalLifecycleState], new_state: SignalLifecycleState, message: str) -> None:
        event = SignalLifecycleEvent(
            event_id=str(uuid.uuid4()),
            signal_id=signal_id,
            event_type=event_type,
            previous_state=prev_state,
            new_state=new_state,
            timestamp=datetime.now(timezone.utc),
            message=message
        )
        self.store.append_event(event)

    def expire_stale_signals(self, now: Optional[datetime] = None) -> List[TrackedSignal]:
        if now is None:
            now = datetime.now(timezone.utc)

        grace = timedelta(minutes=getattr(self.settings, "SIGNAL_STALE_GRACE_MINUTES", 60))
        signals = self.store.load_signals(limit=5000)
        expired = []

        for s in signals:
            if s.state in [SignalLifecycleState.EXPIRED, SignalLifecycleState.INVALIDATED, SignalLifecycleState.COMPLETED, SignalLifecycleState.ARCHIVED]:
                continue
            if s.valid_until and s.valid_until + grace < now:
                prev = s.state
                s.state = SignalLifecycleState.EXPIRED
                s.updated_at = now
                self.store.update_signal(s)
                self._append_event(s.signal_id, SignalLifecycleEventType.EXPIRED, prev, s.state, "Signal expired due to validity window")
                expired.append(s)
        return expired

    def invalidate_signal(self, signal_id: str, reason: str, confirm: bool = False) -> TrackedSignal:
        if not confirm and getattr(self.settings, "SIGNAL_REQUIRE_CONFIRM_FOR_MANUAL_STATE_CHANGE", True):
            raise ValueError("Confirm flag required to invalidate signal")

        s = self.store.get_signal(signal_id)
        if not s:
            raise ValueError(f"Signal not found: {signal_id}")

        prev = s.state
        s.state = SignalLifecycleState.INVALIDATED
        s.updated_at = datetime.now(timezone.utc)
        s.warnings.append(f"Invalidated: {reason}")

        self.store.update_signal(s)
        self._append_event(s.signal_id, SignalLifecycleEventType.INVALIDATED, prev, s.state, f"Manually invalidated: {reason}")
        return s

    def archive_signal(self, signal_id: str, confirm: bool = False) -> TrackedSignal:
        if not confirm and getattr(self.settings, "SIGNAL_REQUIRE_CONFIRM_FOR_ARCHIVE", True):
            raise ValueError("Confirm flag required to archive signal")

        s = self.store.get_signal(signal_id)
        if not s:
            raise ValueError(f"Signal not found: {signal_id}")

        prev = s.state
        s.state = SignalLifecycleState.ARCHIVED
        s.updated_at = datetime.now(timezone.utc)

        self.store.update_signal(s)
        self._append_event(s.signal_id, SignalLifecycleEventType.ARCHIVED, prev, s.state, "Manually archived")
        return s

    def transition(self, signal_id: str, new_state: SignalLifecycleState, message: str, confirm: bool = False) -> TrackedSignal:
        if not confirm and getattr(self.settings, "SIGNAL_REQUIRE_CONFIRM_FOR_MANUAL_STATE_CHANGE", True):
            raise ValueError("Confirm flag required for manual transition")

        s = self.store.get_signal(signal_id)
        if not s:
            raise ValueError(f"Signal not found: {signal_id}")

        prev = s.state
        s.state = new_state
        s.updated_at = datetime.now(timezone.utc)

        self.store.update_signal(s)
        self._append_event(s.signal_id, SignalLifecycleEventType.UPDATED, prev, s.state, f"Manual transition: {message}")
        return s

    def summary(self) -> SignalLifecycleSummary:
        signals = self.store.load_signals(limit=10000)
        summary = SignalLifecycleSummary(generated_at=datetime.now(timezone.utc), total_signals=len(signals))

        for s in signals:
            if s.state == SignalLifecycleState.ACTIVE: summary.active_count += 1
            elif s.state == SignalLifecycleState.WATCHING: summary.watching_count += 1
            elif s.state == SignalLifecycleState.MUTED: summary.muted_count += 1
            elif s.state == SignalLifecycleState.EXPIRED: summary.expired_count += 1
            elif s.state == SignalLifecycleState.INVALIDATED: summary.invalidated_count += 1
            elif s.state == SignalLifecycleState.COMPLETED: summary.completed_count += 1

            if s.watchlist: summary.watchlist_count += 1

            summary.alerts_sent += s.alert_count

        return summary

    def route_to_telegram_inbox(self, evaluation_result, settings=None):
        if not settings or not getattr(settings, 'ENABLE_TELEGRAM_CENTER', False):
            return

        try:
            from bist_signal_bot.app.telegram_center_app import create_notification_inbox
            from bist_signal_bot.telegram_center.models import NotificationMessage, NotificationStatus, NotificationPriority
            import uuid
            from datetime import datetime

            inbox = create_notification_inbox(settings)

            status = NotificationStatus.PENDING
            if evaluation_result.action.value in ["MUTE_COOLDOWN", "MUTE_UNCHANGED", "MUTE_EXPIRED"]:
                status = NotificationStatus.MUTED

            msg = NotificationMessage(
                notification_id=str(uuid.uuid4()),
                title=f"Signal Update: {evaluation_result.signal.symbol}",
                body=f"Action: {evaluation_result.action.value}\nReason: {evaluation_result.reason}",
                priority=NotificationPriority.NORMAL,
                status=status,
                created_at=datetime.utcnow(),
                source="signal_lifecycle",
                dedupe_key=f"sig_{evaluation_result.signal.signal_id}"
            )

            inbox.add_message(msg)
        except Exception as e:
            # gracefully ignore missing telegram center dependencies
            pass
