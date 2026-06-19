import json
import pytest
from pathlib import Path
from bist_signal_bot.signals.policy import SignalPolicyManager
from bist_signal_bot.signals.models import SignalAlertPolicy, SignalPriority
from bist_signal_bot.config.settings import Settings

def test_default_alert_policy():
    manager = SignalPolicyManager()

    # Test with default settings
    policy = manager.default_alert_policy()
    assert isinstance(policy, SignalAlertPolicy)
    assert policy.dedupe_enabled is True
    assert policy.cooldown_minutes == 240
    assert policy.digest_only_below_priority == SignalPriority.NORMAL

    # Test with custom settings
    custom_settings = Settings(
        SIGNAL_ALERT_COOLDOWN_MINUTES=120,
        SIGNAL_DIGEST_ONLY_BELOW_PRIORITY="HIGH",
        SIGNAL_MUTE_LOW_AGREEMENT=False
    )
    policy_custom = manager.default_alert_policy(settings=custom_settings)
    assert policy_custom.cooldown_minutes == 120
    assert policy_custom.digest_only_below_priority == SignalPriority.HIGH
    assert policy_custom.mute_low_agreement is False

    # Test with invalid priority string in settings falls back to NORMAL
    invalid_settings = Settings(
        SIGNAL_DIGEST_ONLY_BELOW_PRIORITY="INVALID_PRIO"
    )
    policy_invalid = manager.default_alert_policy(settings=invalid_settings)
    assert policy_invalid.digest_only_below_priority == SignalPriority.NORMAL


def test_load_alert_policy(tmp_path):
    manager = SignalPolicyManager()

    # 1. Missing file -> falls back to default
    policy1 = manager.load_alert_policy(path=tmp_path / "nonexistent.json")
    assert policy1.cooldown_minutes == 240 # Default value

    # 2. Invalid JSON -> falls back to default
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{ not valid json }")
    policy2 = manager.load_alert_policy(path=invalid_file)
    assert policy2.cooldown_minutes == 240

    # 3. Valid JSON
    valid_data = {
        "cooldown_minutes": 60,
        "validity_minutes": 120,
        "max_alerts_per_signal": 5,
        "digest_only_below_priority": "CRITICAL"
    }
    valid_file = tmp_path / "valid.json"
    valid_file.write_text(json.dumps(valid_data))

    policy3 = manager.load_alert_policy(path=valid_file)
    assert policy3.cooldown_minutes == 60
    assert policy3.validity_minutes == 120
    assert policy3.max_alerts_per_signal == 5
    assert policy3.digest_only_below_priority == SignalPriority.CRITICAL

def test_save_alert_policy(tmp_path):
    manager = SignalPolicyManager()
    policy = SignalAlertPolicy(
        cooldown_minutes=123,
        digest_only_below_priority=SignalPriority.HIGH
    )

    save_path = tmp_path / "saved_policy.json"

    # Needs confirm=True
    with pytest.raises(ValueError, match="Confirm flag must be True to save policy"):
        manager.save_alert_policy(policy, path=save_path, confirm=False)

    # Successful save
    res_path = manager.save_alert_policy(policy, path=save_path, confirm=True)
    assert res_path == save_path
    assert save_path.exists()

    saved_data = json.loads(save_path.read_text())
    assert saved_data["cooldown_minutes"] == 123
    assert saved_data["digest_only_below_priority"] == "HIGH"

def test_validate_policy():
    manager = SignalPolicyManager()

    # Valid policy
    valid_policy = SignalAlertPolicy()
    manager.validate_policy(valid_policy) # Should not raise

    # Invalid cooldown_minutes
    with pytest.raises(ValueError, match="cooldown_minutes must be positive"):
        p = SignalAlertPolicy(cooldown_minutes=0)
        manager.validate_policy(p)

    with pytest.raises(ValueError, match="cooldown_minutes must be positive"):
        p = SignalAlertPolicy(cooldown_minutes=-5)
        manager.validate_policy(p)

    # Invalid validity_minutes
    with pytest.raises(ValueError, match="validity_minutes must be positive"):
        p = SignalAlertPolicy(validity_minutes=0)
        manager.validate_policy(p)

    # Invalid max_alerts_per_signal
    with pytest.raises(ValueError, match="max_alerts_per_signal must be positive"):
        p = SignalAlertPolicy(max_alerts_per_signal=0)
        manager.validate_policy(p)

    # Invalid min_score_change_for_repeat_alert
    with pytest.raises(ValueError, match="min_score_change_for_repeat_alert must be between 0 and 100"):
        p = SignalAlertPolicy(min_score_change_for_repeat_alert=-1)
        manager.validate_policy(p)

    with pytest.raises(ValueError, match="min_score_change_for_repeat_alert must be between 0 and 100"):
        p = SignalAlertPolicy(min_score_change_for_repeat_alert=101)
        manager.validate_policy(p)

    # Invalid min_confidence_for_alert
    with pytest.raises(ValueError, match="min_confidence_for_alert must be between 0 and 100"):
        p = SignalAlertPolicy(min_confidence_for_alert=-1)
        manager.validate_policy(p)

    with pytest.raises(ValueError, match="min_confidence_for_alert must be between 0 and 100"):
        p = SignalAlertPolicy(min_confidence_for_alert=101)
        manager.validate_policy(p)

class MockSignal:
    def __init__(self, score=0, confidence=0, risk_decision=None, warnings=None):
        self.score = score
        self.confidence = confidence
        self.risk_decision = risk_decision
        self.warnings = warnings or []

def test_priority_from_signal():
    manager = SignalPolicyManager()

    # 1. Security warning -> LOW
    s1 = MockSignal(score=100, confidence=100, risk_decision="PASS", warnings=["critical security issue"])
    assert manager.priority_from_signal(s1) == SignalPriority.LOW

    # 2. Risk decision conflict -> LOW
    s2 = MockSignal(score=100, confidence=100, risk_decision="CONFLICT")
    assert manager.priority_from_signal(s2) == SignalPriority.LOW

    s3 = MockSignal(score=100, confidence=100, risk_decision="HIGH_CONFLICT")
    assert manager.priority_from_signal(s3) == SignalPriority.LOW

    # 3. Stale warning -> LOW
    s4 = MockSignal(score=100, confidence=100, risk_decision="PASS", warnings=["data is stale"])
    assert manager.priority_from_signal(s4) == SignalPriority.LOW

    # 4. HIGH Priority conditions (score >= 85, confidence >= 80, PASS)
    s5 = MockSignal(score=85, confidence=80, risk_decision="PASS")
    assert manager.priority_from_signal(s5) == SignalPriority.HIGH

    s6 = MockSignal(score=90, confidence=90, risk_decision="PASS")
    assert manager.priority_from_signal(s6) == SignalPriority.HIGH

    # Not quite HIGH because of score/confidence/risk_decision
    s7 = MockSignal(score=84, confidence=80, risk_decision="PASS")
    assert manager.priority_from_signal(s7) == SignalPriority.NORMAL

    s8 = MockSignal(score=85, confidence=79, risk_decision="PASS")
    assert manager.priority_from_signal(s8) == SignalPriority.NORMAL

    s9 = MockSignal(score=85, confidence=80, risk_decision="UNKNOWN")
    assert manager.priority_from_signal(s9) == SignalPriority.NORMAL

    # 5. NORMAL Priority conditions (score >= 60)
    s10 = MockSignal(score=60, confidence=50, risk_decision="UNKNOWN")
    assert manager.priority_from_signal(s10) == SignalPriority.NORMAL

    # 6. Default LOW
    s11 = MockSignal(score=59, confidence=100, risk_decision="PASS")
    assert manager.priority_from_signal(s11) == SignalPriority.LOW
