import pytest
from bist_signal_bot.calibration.models import OutcomeRecord, CalibrationResult, CalibrationStatus

def test_outcome_record_symbol_normalization():
    record = OutcomeRecord(
        outcome_id="test1",
        symbol="asels.IS",
        generated_at="2023-01-01T00:00:00Z"
    )
    assert record.symbol == "ASELS"

def test_outcome_record_score_clamp():
    record = OutcomeRecord(
        outcome_id="test2",
        symbol="THYAO",
        generated_at="2023-01-01T00:00:00Z",
        raw_score=150.0,
        confidence_score=-10.0
    )
    assert record.raw_score == 100.0
    assert record.confidence_score == 0.0

def test_calibration_result_default_status():
    res = CalibrationResult(
        calibration_id="test",
        score_type="SIGNAL_CONFIDENCE",
        horizon="FIVE_DAYS"
    )
    assert res.status == CalibrationStatus.UNKNOWN
