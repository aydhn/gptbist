import pytest
from bist_signal_bot.calibration.error_taxonomy import ErrorTaxonomyBuilder
from bist_signal_bot.calibration.models import OutcomeRecord, CalibrationScoreType, OutcomeLabel, ErrorCaseType
from datetime import datetime, UTC

def test_classify_high_confidence_failure():
    builder = ErrorTaxonomyBuilder()
    record = OutcomeRecord(
        outcome_id="1", symbol="A", generated_at=datetime.now(UTC),
        confidence_score=90.0, outcome_label=OutcomeLabel.FAILURE, net_return_pct=-6.0
    )
    cases = builder.classify_record(record, CalibrationScoreType.SIGNAL_CONFIDENCE, 75.0, 35.0)
    assert len(cases) == 1
    assert cases[0].error_type == ErrorCaseType.HIGH_CONFIDENCE_FAILURE
    assert cases[0].severity == "CRITICAL"

def test_classify_execution_drag():
    builder = ErrorTaxonomyBuilder()
    record = OutcomeRecord(
        outcome_id="1", symbol="A", generated_at=datetime.now(UTC),
        outcome_label=OutcomeLabel.SUCCESS, cost_drag_pct=1.5
    )
    cases = builder.classify_record(record, CalibrationScoreType.SIGNAL_CONFIDENCE, 75.0, 35.0)
    assert any(c.error_type == ErrorCaseType.EXECUTION_COST_DRAG for c in cases)
