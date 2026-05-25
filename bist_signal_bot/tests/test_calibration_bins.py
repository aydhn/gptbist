import pytest
from bist_signal_bot.calibration.bins import CalibrationBinBuilder
from bist_signal_bot.calibration.models import OutcomeRecord, CalibrationScoreType, OutcomeLabel
from datetime import datetime, UTC

def test_assign_bin():
    builder = CalibrationBinBuilder()
    assert builder.assign_bin(45.5, 10) == (40.0, 50.0)
    assert builder.assign_bin(100.0, 10) == (90.0, 100.0)
    assert builder.assign_bin(150.0, 10) == (90.0, 100.0)

def test_build_bins():
    builder = CalibrationBinBuilder()
    builder.settings.CALIBRATION_MERGE_SPARSE_BINS = False

    records = [
        OutcomeRecord(outcome_id="1", symbol="A", generated_at=datetime.now(UTC), confidence_score=45.0, outcome_label=OutcomeLabel.SUCCESS),
        OutcomeRecord(outcome_id="2", symbol="A", generated_at=datetime.now(UTC), confidence_score=46.0, outcome_label=OutcomeLabel.FAILURE)
    ]

    bins = builder.build_bins(records, CalibrationScoreType.SIGNAL_CONFIDENCE, bin_size=10)
    b_40_50 = next(b for b in bins if b.lower_bound == 40.0)
    assert b_40_50.sample_count == 2
    assert b_40_50.success_count == 1
    assert b_40_50.observed_success_rate == 0.5
