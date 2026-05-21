import pytest
from bist_signal_bot.drift.signal_decay import SignalDecayAnalyzer
from bist_signal_bot.drift.models import DriftStatus, DriftSeverity
from bist_signal_bot.config.settings import Settings

def test_signal_decay_insufficient():
    s = Settings()
    s.DRIFT_MIN_SAMPLES = 50
    sda = SignalDecayAnalyzer(s)
    res = sda.analyze([], [])
    assert res.status == DriftStatus.INSUFFICIENT_DATA

def test_signal_decay_drop_outcome():
    s = Settings()
    s.DRIFT_MIN_SAMPLES = 2
    s.DRIFT_SIGNAL_OUTCOME_DROP_FAIL = 40.0
    sda = SignalDecayAnalyzer(s)

    # 100% positive
    ref = [{"alert_sent": True, "outcome_positive": True}] * 10
    # 50% positive -> 50% drop
    cur = [{"alert_sent": True, "outcome_positive": True}] * 5 + [{"alert_sent": True, "outcome_positive": False}] * 5

    res = sda.analyze(ref, cur)
    assert res.status == DriftStatus.DRIFTING
    assert res.severity == DriftSeverity.HIGH
