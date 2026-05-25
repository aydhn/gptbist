import pytest
from bist_signal_bot.calibration.cohorts import OutcomeCohortAnalyzer
from bist_signal_bot.calibration.models import OutcomeRecord, CalibrationScoreType, OutcomeLabel, CalibrationStatus
from datetime import datetime, UTC

def test_cohort_by_field():
    analyzer = OutcomeCohortAnalyzer()
    analyzer.settings.CALIBRATION_MIN_COHORT_SAMPLES = 2
    records = [
        OutcomeRecord(outcome_id="1", symbol="ASELS", generated_at=datetime.now(UTC), strategy_name="S1", outcome_label=OutcomeLabel.SUCCESS, confidence_score=50.0),
        OutcomeRecord(outcome_id="2", symbol="THYAO", generated_at=datetime.now(UTC), strategy_name="S1", outcome_label=OutcomeLabel.FAILURE, confidence_score=50.0)
    ]
    cohorts = analyzer.cohort_by_field(records, "strategy_name", CalibrationScoreType.SIGNAL_CONFIDENCE)
    assert len(cohorts) == 1
    c = cohorts[0]
    assert c.name == "strategy_name:S1"
    assert c.sample_count == 2
    assert c.success_rate == 0.5
    assert c.status == CalibrationStatus.PASS
