import pytest
from bist_signal_bot.calibration.calibrator import SignalCalibrator
from bist_signal_bot.calibration.models import OutcomeRecord, CalibrationScoreType, OutcomeLabel, CalibratorMapping
from datetime import datetime, UTC

def test_fit_insufficient_samples():
    calibrator = SignalCalibrator()
    calibrator.settings.CALIBRATION_MIN_RECORDS = 50
    records = [OutcomeRecord(outcome_id="1", symbol="A", generated_at=datetime.now(UTC))]
    mapping = calibrator.fit(records, CalibrationScoreType.SIGNAL_CONFIDENCE)
    assert mapping.method == "identity"

def test_calibrate_score():
    calibrator = SignalCalibrator()
    mapping = CalibratorMapping(
        mapping_id="m1",
        score_type=CalibrationScoreType.SIGNAL_CONFIDENCE,
        method="binning",
        bin_mappings={"80.0-90.0": 65.0}
    )
    assert calibrator.calibrate_score(85.0, mapping) == 65.0
    assert calibrator.calibrate_score(50.0, mapping) == 50.0 # fallback
