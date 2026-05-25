from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.calibration.storage import CalibrationStore
from bist_signal_bot.calibration.outcomes import OutcomeDatasetBuilder
from bist_signal_bot.calibration.bins import CalibrationBinBuilder
from bist_signal_bot.calibration.metrics import CalibrationMetricsCalculator
from bist_signal_bot.calibration.reliability import ReliabilityCurveBuilder
from bist_signal_bot.calibration.calibrator import SignalCalibrator
from bist_signal_bot.calibration.thresholds import ThresholdTuner
from bist_signal_bot.calibration.cohorts import OutcomeCohortAnalyzer
from bist_signal_bot.calibration.error_taxonomy import ErrorTaxonomyBuilder
from bist_signal_bot.calibration.scoring import CalibrationScorer

def create_calibration_store(settings: Settings | None = None, base_dir: Path | None = None) -> CalibrationStore:
    return CalibrationStore(settings=settings, base_dir=base_dir)

def create_outcome_dataset_builder(settings: Settings | None = None, base_dir: Path | None = None) -> OutcomeDatasetBuilder:
    store = create_calibration_store(settings, base_dir)
    return OutcomeDatasetBuilder(settings=settings, store=store)

def create_calibration_bin_builder(settings: Settings | None = None) -> CalibrationBinBuilder:
    return CalibrationBinBuilder(settings=settings)

def create_calibration_metrics_calculator(settings: Settings | None = None) -> CalibrationMetricsCalculator:
    return CalibrationMetricsCalculator(settings=settings)

def create_reliability_curve_builder(settings: Settings | None = None) -> ReliabilityCurveBuilder:
    return ReliabilityCurveBuilder(settings=settings)

def create_signal_calibrator(settings: Settings | None = None) -> SignalCalibrator:
    return SignalCalibrator(settings=settings)

def create_threshold_tuner(settings: Settings | None = None) -> ThresholdTuner:
    return ThresholdTuner(settings=settings)

def create_outcome_cohort_analyzer(settings: Settings | None = None) -> OutcomeCohortAnalyzer:
    return OutcomeCohortAnalyzer(settings=settings)

def create_error_taxonomy_builder(settings: Settings | None = None) -> ErrorTaxonomyBuilder:
    return ErrorTaxonomyBuilder(settings=settings)

def create_calibration_scorer(settings: Settings | None = None) -> CalibrationScorer:
    return CalibrationScorer(settings=settings)
