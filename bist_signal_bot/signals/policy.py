import json
from pathlib import Path
from typing import Optional, Any
from bist_signal_bot.signals.models import SignalAlertPolicy, SignalPriority
from bist_signal_bot.config.settings import Settings

class SignalPolicyManager:
    def default_alert_policy(self, settings: Optional[Settings] = None) -> SignalAlertPolicy:
        if settings is None:
            from bist_signal_bot.config.settings import get_settings
            settings = get_settings()

        priority_str = getattr(settings, "SIGNAL_DIGEST_ONLY_BELOW_PRIORITY", "NORMAL")
        try:
            digest_only_priority = SignalPriority(priority_str)
        except ValueError:
            digest_only_priority = SignalPriority.NORMAL

        return SignalAlertPolicy(
            dedupe_enabled=getattr(settings, "SIGNAL_ALERT_DEDUPE_ENABLED", True),
            cooldown_minutes=getattr(settings, "SIGNAL_ALERT_COOLDOWN_MINUTES", 240),
            validity_minutes=getattr(settings, "SIGNAL_VALIDITY_MINUTES", 1440),
            min_score_change_for_repeat_alert=getattr(settings, "SIGNAL_MIN_SCORE_CHANGE_FOR_REPEAT_ALERT", 7.5),
            min_confidence_for_alert=getattr(settings, "SIGNAL_MIN_CONFIDENCE_FOR_ALERT", 45.0),
            max_alerts_per_signal=getattr(settings, "SIGNAL_MAX_ALERTS_PER_SIGNAL", 3),
            digest_only_below_priority=digest_only_priority,
            mute_low_agreement=getattr(settings, "SIGNAL_MUTE_LOW_AGREEMENT", True),
            mute_high_conflict=getattr(settings, "SIGNAL_MUTE_HIGH_CONFLICT", True),
            allow_critical_repeat=getattr(settings, "SIGNAL_ALLOW_CRITICAL_REPEAT_ALERT", True)
        )

    def load_alert_policy(self, path: Optional[Path] = None) -> SignalAlertPolicy:
        if path and path.exists():
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                return SignalAlertPolicy(**data)
            except Exception:
                pass
        return self.default_alert_policy()

    def save_alert_policy(self, policy: SignalAlertPolicy, path: Optional[Path] = None, confirm: bool = False) -> Path:
        if path is None:
            from bist_signal_bot.storage.paths import get_signals_dir
            path = get_signals_dir() / "policy" / "alert_policy.json"

        if not confirm:
            raise ValueError("Confirm flag must be True to save policy")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(policy.model_dump_json(indent=2), encoding='utf-8')
        return path

    def validate_policy(self, policy: SignalAlertPolicy) -> None:
        if policy.cooldown_minutes <= 0:
            raise ValueError("cooldown_minutes must be positive")
        if policy.validity_minutes <= 0:
            raise ValueError("validity_minutes must be positive")
        if policy.max_alerts_per_signal <= 0:
            raise ValueError("max_alerts_per_signal must be positive")
        if not (0 <= policy.min_score_change_for_repeat_alert <= 100):
            raise ValueError("min_score_change_for_repeat_alert must be between 0 and 100")
        if not (0 <= policy.min_confidence_for_alert <= 100):
            raise ValueError("min_confidence_for_alert must be between 0 and 100")

    def priority_from_signal(self, signal: Any) -> SignalPriority:
        score = getattr(signal, 'score', 0) or getattr(signal, 'current_score', 0)
        confidence = getattr(signal, 'confidence', 0)
        risk_decision = getattr(signal, 'risk_decision', None)

        warnings = getattr(signal, 'warnings', [])
        is_stale = any('stale' in w.lower() for w in warnings)
        has_security_warning = any('security' in w.lower() for w in warnings)

        if has_security_warning:
            return SignalPriority.LOW

        if risk_decision in ["CONFLICT", "HIGH_CONFLICT"] or is_stale:
            return SignalPriority.LOW

        if score >= 85 and confidence >= 80 and risk_decision == "PASS":
            return SignalPriority.HIGH

        if score >= 60:
            return SignalPriority.NORMAL

        return SignalPriority.LOW
