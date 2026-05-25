import pytest
from bist_signal_bot.calibration.metrics import CalibrationMetricsCalculator
from bist_signal_bot.calibration.models import OutcomeRecord, CalibrationBin, CalibrationScoreType, OutcomeLabel
from datetime import datetime, UTC

def test_brier_score():
    calc = CalibrationMetricsCalculator()
    records = [
        OutcomeRecord(outcome_id="1", symbol="A", generated_at=datetime.now(UTC), confidence_score=80.0, outcome_label=OutcomeLabel.SUCCESS), # 0.8 vs 1.0 = 0.04
        OutcomeRecord(outcome_id="2", symbol="A", generated_at=datetime.now(UTC), confidence_score=20.0, outcome_label=OutcomeLabel.FAILURE)  # 0.2 vs 0.0 = 0.04
    ]
    brier = calc.brier_score(records, CalibrationScoreType.SIGNAL_CONFIDENCE)
    assert brier == pytest.approx(0.04)

def test_expected_calibration_error():
    calc = CalibrationMetricsCalculator()
    bins = [
        CalibrationBin(bin_id="b1", score_type=CalibrationScoreType.SIGNAL_CONFIDENCE, lower_bound=0, upper_bound=50, sample_count=50, calibration_gap=0.1),
        CalibrationBin(bin_id="b2", score_type=CalibrationScoreType.SIGNAL_CONFIDENCE, lower_bound=50, upper_bound=100, sample_count=50, calibration_gap=-0.2)
    ]
    ece = calc.expected_calibration_error(bins)
    assert ece == pytest.approx((0.5 * 0.1) + (0.5 * 0.2))

def test_hit_rate():
    calc = CalibrationMetricsCalculator()
    records = [
        OutcomeRecord(outcome_id="1", symbol="A", generated_at=datetime.now(UTC), outcome_label=OutcomeLabel.SUCCESS),
        OutcomeRecord(outcome_id="2", symbol="A", generated_at=datetime.now(UTC), outcome_label=OutcomeLabel.FAILURE),
        OutcomeRecord(outcome_id="3", symbol="A", generated_at=datetime.now(UTC), outcome_label=OutcomeLabel.NEUTRAL)
    ]
    assert calc.hit_rate(records) == 0.5
