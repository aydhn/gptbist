import pytest
import pandas as pd
from bist_signal_bot.drift.feature_drift import FeatureDriftDetector
from bist_signal_bot.drift.models import DriftStatus, DriftSeverity
from bist_signal_bot.config.settings import Settings

def test_feature_drift_numeric():
    s = Settings()
    s.DRIFT_MIN_SAMPLES = 5
    det = FeatureDriftDetector(s)

    ref = pd.DataFrame({"f1": [1.0, 1.2, 1.1, 1.3, 1.0, 1.2]})
    cur = pd.DataFrame({"f1": [5.0, 5.2, 5.1, 5.3, 5.0, 5.2]}) # Severe shift

    res = det.detect(ref, cur, ["f1"])
    assert len(res) == 1
    assert res[0].status == DriftStatus.SEVERE_DRIFT
    assert res[0].severity == DriftSeverity.CRITICAL

def test_feature_drift_insufficient():
    s = Settings()
    s.DRIFT_MIN_SAMPLES = 50
    det = FeatureDriftDetector(s)

    ref = pd.DataFrame({"f1": [1.0, 1.2]})
    cur = pd.DataFrame({"f1": [1.0, 1.2]})

    res = det.detect(ref, cur, ["f1"])
    assert res[0].status == DriftStatus.INSUFFICIENT_DATA
