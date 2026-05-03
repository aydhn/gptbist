import pytest
from bist_signal_bot.signals.models import SignalDirection, SignalStrength
from bist_signal_bot.signals.scoring import classify_signal_strength, safe_risk_reward

def test_classify_signal_strength():
    assert classify_signal_strength(10.0) == SignalStrength.VERY_WEAK
    assert classify_signal_strength(30.0) == SignalStrength.WEAK
    assert classify_signal_strength(50.0) == SignalStrength.MODERATE
    assert classify_signal_strength(70.0) == SignalStrength.STRONG
    assert classify_signal_strength(90.0) == SignalStrength.VERY_STRONG

    # Check clamping
    assert classify_signal_strength(150.0) == SignalStrength.VERY_STRONG
    assert classify_signal_strength(-50.0) == SignalStrength.VERY_WEAK

def test_safe_risk_reward():
    # Long
    rr = safe_risk_reward(entry=100.0, stop=90.0, target=120.0, direction=SignalDirection.LONG)
    assert rr == 2.0  # (120-100) / (100-90) = 20 / 10 = 2

    # Short
    rr = safe_risk_reward(entry=100.0, stop=110.0, target=80.0, direction=SignalDirection.SHORT)
    assert rr == 2.0  # (100-80) / (110-100) = 20 / 10 = 2

    # Invalid
    assert safe_risk_reward(entry=100.0, stop=110.0, target=120.0, direction=SignalDirection.LONG) is None
    assert safe_risk_reward(None, 90.0, 120.0, SignalDirection.LONG) is None
