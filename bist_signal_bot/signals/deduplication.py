from datetime import datetime, timezone
from typing import List, Optional
from bist_signal_bot.signals.models import (
    TrackedSignal, SignalAlertPolicy, AlertEvaluationResult,
    SignalAlertDecision, SignalPriority
)

class SignalDeduplicator:
    def evaluate_alert(self, signal: TrackedSignal, previous: Optional[TrackedSignal],
                       policy: SignalAlertPolicy, now: Optional[datetime] = None) -> AlertEvaluationResult:
        if now is None:
            now = datetime.now(timezone.utc)

        reason = ""
        decision = SignalAlertDecision.SEND
        cooldown_rem = None

        if previous is None:
            reason = "New signal"
            decision = SignalAlertDecision.SEND
        else:
            cooldown_rem = self.cooldown_remaining(previous, policy.cooldown_minutes, now)
            if cooldown_rem > 0:
                reason = f"In cooldown ({cooldown_rem:.1f} mins left)"
                decision = SignalAlertDecision.MUTE_COOLDOWN

                # Check for critical repeat override
                if policy.allow_critical_repeat and signal.priority == SignalPriority.CRITICAL:
                    if self.score_changed_enough(previous, signal, policy.min_score_change_for_repeat_alert):
                        decision = SignalAlertDecision.SEND
                        reason = "Critical signal with sufficient score change override"
            else:
                if not self.score_changed_enough(previous, signal, policy.min_score_change_for_repeat_alert):
                    reason = "Score unchanged or insufficient change"
                    decision = SignalAlertDecision.MUTE_UNCHANGED
                else:
                    reason = "Cooldown expired and score changed"
                    decision = SignalAlertDecision.SEND

        if decision == SignalAlertDecision.SEND:
            if previous and previous.alert_count >= policy.max_alerts_per_signal:
                if policy.dedupe_enabled:
                    decision = SignalAlertDecision.MUTE_DUPLICATE
                    reason = "Max alerts reached"
                else:
                    decision = SignalAlertDecision.SEND_DIGEST_ONLY
                    reason = "Max alerts reached but dedupe is false (digest only)"
            elif policy.mute_high_conflict and signal.risk_decision in ["HIGH_CONFLICT"]:
                decision = SignalAlertDecision.MUTE_HIGH_CONFLICT
                reason = "High conflict risk decision"
            elif self._priority_too_low(signal.priority, policy.digest_only_below_priority):
                decision = SignalAlertDecision.SEND_DIGEST_ONLY
                reason = "Low priority signal"

        should_send = decision in [SignalAlertDecision.SEND, SignalAlertDecision.SEND_DIGEST_ONLY]
        should_add_to_digest = decision in [SignalAlertDecision.SEND, SignalAlertDecision.SEND_DIGEST_ONLY, SignalAlertDecision.MUTE_COOLDOWN]

        return AlertEvaluationResult(
            signal_id=signal.signal_id,
            fingerprint_id=signal.fingerprint_id,
            decision=decision,
            should_send=should_send,
            should_add_to_digest=should_add_to_digest,
            reason=reason,
            cooldown_remaining_minutes=cooldown_rem,
            previous_signal_id=previous.signal_id if previous else None
        )

    def _priority_too_low(self, priority: SignalPriority, threshold: SignalPriority) -> bool:
        order = {SignalPriority.LOW: 1, SignalPriority.NORMAL: 2, SignalPriority.HIGH: 3, SignalPriority.CRITICAL: 4}
        p_val = order.get(priority, 0)
        t_val = order.get(threshold, 0)
        return p_val < t_val

    def score_changed_enough(self, previous: TrackedSignal, current: TrackedSignal, min_change: float) -> bool:
        prev_score = previous.current_score or 0
        curr_score = current.current_score or 0
        return abs(curr_score - prev_score) >= min_change

    def cooldown_remaining(self, previous: TrackedSignal, cooldown_minutes: int, now: datetime) -> float:
        if not previous.last_alert_at:
            return 0.0
        elapsed = (now - previous.last_alert_at).total_seconds() / 60.0
        rem = cooldown_minutes - elapsed
        return max(0.0, rem)

    def merge_duplicate_signals(self, signals: List[TrackedSignal]) -> List[TrackedSignal]:
        # Merge by fingerprint_id, keep latest
        merged = {}
        for s in signals:
            if s.fingerprint_id not in merged or s.updated_at > merged[s.fingerprint_id].updated_at:
                merged[s.fingerprint_id] = s
        return list(merged.values())
