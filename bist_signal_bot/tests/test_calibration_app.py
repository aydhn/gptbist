from bist_signal_bot.app.calibration_app import (
    create_calibration_store,
    create_outcome_dataset_builder,
    create_calibration_bin_builder,
    create_calibration_metrics_calculator,
    create_reliability_curve_builder,
    create_signal_calibrator,
    create_threshold_tuner,
    create_outcome_cohort_analyzer,
    create_error_taxonomy_builder,
    create_calibration_scorer
)
from bist_signal_bot.config.settings import Settings

def test_create_calibration_store():
    store = create_calibration_store()
    assert type(store).__name__ == "CalibrationStore"

def test_create_outcome_dataset_builder():
    builder = create_outcome_dataset_builder()
    assert type(builder).__name__ == "OutcomeDatasetBuilder"

def test_create_calibration_bin_builder():
    builder = create_calibration_bin_builder()
    assert type(builder).__name__ == "CalibrationBinBuilder"

def test_create_calibration_metrics_calculator():
    calc = create_calibration_metrics_calculator()
    assert type(calc).__name__ == "CalibrationMetricsCalculator"

def test_create_reliability_curve_builder():
    builder = create_reliability_curve_builder()
    assert type(builder).__name__ == "ReliabilityCurveBuilder"

def test_create_signal_calibrator():
    calibrator = create_signal_calibrator()
    assert type(calibrator).__name__ == "SignalCalibrator"

def test_create_threshold_tuner():
    tuner = create_threshold_tuner()
    assert type(tuner).__name__ == "ThresholdTuner"

def test_create_outcome_cohort_analyzer():
    analyzer = create_outcome_cohort_analyzer()
    assert type(analyzer).__name__ == "OutcomeCohortAnalyzer"

def test_create_error_taxonomy_builder():
    builder = create_error_taxonomy_builder()
    assert type(builder).__name__ == "ErrorTaxonomyBuilder"

def test_create_calibration_scorer():
    scorer = create_calibration_scorer()
    assert type(scorer).__name__ == "CalibrationScorer"
    assert isinstance(scorer.settings, Settings)

def test_create_calibration_scorer_with_settings():
    settings = Settings()
    scorer = create_calibration_scorer(settings=settings)
    assert type(scorer).__name__ == "CalibrationScorer"
    assert scorer.settings == settings
