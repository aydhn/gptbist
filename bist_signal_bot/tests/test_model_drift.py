import pytest
import pandas as pd
from bist_signal_bot.drift.model_drift import ModelDriftDetector
from bist_signal_bot.drift.models import DriftStatus, DriftSeverity
from bist_signal_bot.config.settings import Settings

def test_model_drift_detect_missing_col():
    s = Settings()
    det = ModelDriftDetector(s)
    ref = pd.DataFrame({"score": [0.5, 0.6]})
    cur = pd.DataFrame({"score": [0.5, 0.6]})
    res = det.detect_model_drift("m1", ref, cur)
    assert res.status == DriftStatus.ERROR

def test_model_drift_rate_change():
    s = Settings()
    s.DRIFT_MODEL_POSITIVE_RATE_CHANGE_FAIL = 30.0
    det = ModelDriftDetector(s)

    # reference rate: 50%
    ref = pd.DataFrame({"prediction": [0.8, 0.1, 0.9, 0.2]})
    # current rate: 100% -> change is 100% > 30% -> Fail
    cur = pd.DataFrame({"prediction": [0.8, 0.9, 0.8, 0.9]})

    res = det.detect_model_drift("m1", ref, cur)
    assert res.status == DriftStatus.DRIFTING
    assert res.severity == DriftSeverity.HIGH
