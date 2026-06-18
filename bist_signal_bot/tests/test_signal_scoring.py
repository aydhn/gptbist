import pytest
from bist_signal_bot.signals.scoring import (
    clamp_score,
    classify_signal_strength,
    weighted_score,
    directional_score_to_direction,
    safe_risk_reward,
)
from bist_signal_bot.signals.models import SignalStrength, SignalDirection

def test_clamp_score():
    assert clamp_score(50.0) == 50.0
    assert clamp_score(-10.0) == 0.0
    assert clamp_score(110.0) == 100.0
    assert clamp_score(15.0, min_value=10.0, max_value=20.0) == 15.0
    assert clamp_score(5.0, min_value=10.0, max_value=20.0) == 10.0
    assert clamp_score(25.0, min_value=10.0, max_value=20.0) == 20.0

def test_classify_signal_strength():
    assert classify_signal_strength(10.0) == SignalStrength.VERY_WEAK
    assert classify_signal_strength(20.0) == SignalStrength.VERY_WEAK
    assert classify_signal_strength(30.0) == SignalStrength.WEAK
    assert classify_signal_strength(40.0) == SignalStrength.WEAK
    assert classify_signal_strength(50.0) == SignalStrength.MODERATE
    assert classify_signal_strength(60.0) == SignalStrength.MODERATE
    assert classify_signal_strength(70.0) == SignalStrength.STRONG
    assert classify_signal_strength(80.0) == SignalStrength.STRONG
    assert classify_signal_strength(90.0) == SignalStrength.VERY_STRONG
    assert classify_signal_strength(100.0) == SignalStrength.VERY_STRONG

    # Test clamping
    assert classify_signal_strength(-10.0) == SignalStrength.VERY_WEAK
    assert classify_signal_strength(110.0) == SignalStrength.VERY_STRONG

def test_weighted_score():
    # Empty parts or weights
    assert weighted_score({}, {"a": 1.0}) == 0.0
    assert weighted_score({"a": 1.0}, {}) == 0.0

    # Normal calculation
    parts = {"a": 50.0, "b": 100.0}
    weights = {"a": 0.5, "b": 0.5}
    assert weighted_score(parts, weights) == 75.0

    # Missing key in weights
    weights_missing = {"a": 0.5}
    assert weighted_score(parts, weights_missing) == 50.0

    # Zero total weight
    weights_zero = {"a": 0.0, "b": 0.0}
    assert weighted_score(parts, weights_zero) == 0.0

def test_directional_score_to_direction():
    assert directional_score_to_direction(70.0) == SignalDirection.LONG
    assert directional_score_to_direction(60.0) == SignalDirection.LONG
    assert directional_score_to_direction(-70.0) == SignalDirection.SHORT
    assert directional_score_to_direction(-60.0) == SignalDirection.SHORT
    assert directional_score_to_direction(0.0) == SignalDirection.FLAT
    assert directional_score_to_direction(59.9) == SignalDirection.FLAT
    assert directional_score_to_direction(-59.9) == SignalDirection.FLAT

    # Custom thresholds
    assert directional_score_to_direction(50.0, long_threshold=50.0, short_threshold=-50.0) == SignalDirection.LONG
    assert directional_score_to_direction(-50.0, long_threshold=50.0, short_threshold=-50.0) == SignalDirection.SHORT

def test_safe_risk_reward():
    # Any None -> None
    assert safe_risk_reward(None, 90.0, 120.0, SignalDirection.LONG) is None
    assert safe_risk_reward(100.0, None, 120.0, SignalDirection.LONG) is None
    assert safe_risk_reward(100.0, 90.0, None, SignalDirection.LONG) is None

    # LONG correct calculation
    # Entry = 100, Stop = 90, Target = 120
    # Risk = 10, Reward = 20 -> RR = 2.0
    assert safe_risk_reward(100.0, 90.0, 120.0, SignalDirection.LONG) == 2.0

    # SHORT correct calculation
    # Entry = 100, Stop = 110, Target = 80
    # Risk = 10, Reward = 20 -> RR = 2.0
    assert safe_risk_reward(100.0, 110.0, 80.0, SignalDirection.SHORT) == 2.0

    # Risk <= 0 -> None
    assert safe_risk_reward(100.0, 100.0, 120.0, SignalDirection.LONG) is None
    assert safe_risk_reward(100.0, 110.0, 120.0, SignalDirection.LONG) is None

    # Non-LONG/SHORT -> None
    assert safe_risk_reward(100.0, 90.0, 120.0, SignalDirection.FLAT) is None
    assert safe_risk_reward(100.0, 90.0, 120.0, SignalDirection.WATCH) is None
