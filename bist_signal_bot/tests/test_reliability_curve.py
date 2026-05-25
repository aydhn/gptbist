import pytest
from bist_signal_bot.calibration.reliability import ReliabilityCurveBuilder
from bist_signal_bot.calibration.models import OutcomeRecord, CalibrationScoreType, OutcomeHorizon, OutcomeLabel, CalibrationStatus
from datetime import datetime, UTC

def test_build_curve_insufficient():
    builder = ReliabilityCurveBuilder()
    builder.settings.CALIBRATION_MIN_RECORDS = 50
    records = [
        OutcomeRecord(outcome_id="1", symbol="A", generated_at=datetime.now(UTC), confidence_score=80.0, outcome_label=OutcomeLabel.SUCCESS)
    ]
    curve = builder.build_curve(records, CalibrationScoreType.SIGNAL_CONFIDENCE, OutcomeHorizon.FIVE_DAYS)
    assert curve.status == CalibrationStatus.INSUFFICIENT_DATA
    assert any("small sample size" in w for w in curve.warnings)
