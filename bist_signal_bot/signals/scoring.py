from typing import Any
from bist_signal_bot.signals.models import SignalStrength, SignalDirection

def clamp_score(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    return max(min_value, min(value, max_value))

def classify_signal_strength(score: float) -> SignalStrength:
    score = clamp_score(score)
    if score <= 20.0:
        return SignalStrength.VERY_WEAK
    elif score <= 40.0:
        return SignalStrength.WEAK
    elif score <= 60.0:
        return SignalStrength.MODERATE
    elif score <= 80.0:
        return SignalStrength.STRONG
    else:
        return SignalStrength.VERY_STRONG

def weighted_score(parts: dict[str, float], weights: dict[str, float]) -> float:
    if not parts or not weights:
        return 0.0

    total_score = 0.0
    total_weight = 0.0

    for key, value in parts.items():
        if key in weights:
            weight = weights[key]
            total_score += value * weight
            total_weight += weight

    if total_weight == 0.0:
        return 0.0

    return total_score / total_weight

def directional_score_to_direction(score: float, long_threshold: float = 60.0, short_threshold: float = -60.0) -> SignalDirection:
    if score >= long_threshold:
        return SignalDirection.LONG
    elif score <= short_threshold:
        return SignalDirection.SHORT
    return SignalDirection.FLAT

def safe_risk_reward(entry: float | None, stop: float | None, target: float | None, direction: SignalDirection) -> float | None:
    if entry is None or stop is None or target is None:
        return None

    if direction == SignalDirection.LONG:
        risk = entry - stop
        reward = target - entry
    elif direction == SignalDirection.SHORT:
        risk = stop - entry
        reward = entry - target
    else:
        return None

    if risk <= 0:
        return None

    return reward / risk
