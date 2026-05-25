import pytest
from bist_signal_bot.calibration.thresholds import ThresholdTuner
from bist_signal_bot.calibration.models import OutcomeRecord, CalibrationScoreType, OutcomeHorizon, OutcomeLabel
from datetime import datetime, UTC

def test_evaluate_threshold():
    tuner = ThresholdTuner()
    records = [
        OutcomeRecord(outcome_id="1", symbol="A", generated_at=datetime.now(UTC), confidence_score=80.0, outcome_label=OutcomeLabel.SUCCESS, net_return_pct=2.0),
        OutcomeRecord(outcome_id="2", symbol="A", generated_at=datetime.now(UTC), confidence_score=40.0, outcome_label=OutcomeLabel.FAILURE, net_return_pct=-2.0)
    ]
    eval_75 = tuner.evaluate_threshold(records, CalibrationScoreType.SIGNAL_CONFIDENCE, 75.0)
    assert eval_75["signal_count"] == 1
    assert eval_75["hit_rate"] == 1.0
    assert eval_75["reduction_pct"] == 50.0

def test_candidate_thresholds():
    tuner = ThresholdTuner()
    tuner.settings.CALIBRATION_THRESHOLD_START = 80.0
    tuner.settings.CALIBRATION_THRESHOLD_END = 90.0
    tuner.settings.CALIBRATION_THRESHOLD_STEP = 5.0
    cands = tuner.candidate_thresholds()
    assert cands == [80.0, 85.0, 90.0]
