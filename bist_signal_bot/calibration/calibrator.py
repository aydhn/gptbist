import uuid
from bist_signal_bot.calibration.models import (
    OutcomeRecord, CalibrationScoreType, CalibratorMapping, CalibrationResult,
    OutcomeHorizon, CalibrationStatus
)
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.calibration.bins import CalibrationBinBuilder
from bist_signal_bot.calibration.metrics import CalibrationMetricsCalculator
from bist_signal_bot.calibration.reliability import ReliabilityCurveBuilder

# ContextFusion collects calibration reliability
class SignalCalibrator:
    def __init__(self, settings: Settings | None = None, bin_builder: CalibrationBinBuilder | None = None, metrics_calc: CalibrationMetricsCalculator | None = None, curve_builder: ReliabilityCurveBuilder | None = None):
        self.settings = settings or Settings()
        self.bin_builder = bin_builder or CalibrationBinBuilder(self.settings)
        self.metrics_calc = metrics_calc or CalibrationMetricsCalculator(self.settings)
        self.curve_builder = curve_builder or ReliabilityCurveBuilder(self.settings, self.bin_builder, self.metrics_calc)

    def fit(self, records: list[OutcomeRecord], score_type: CalibrationScoreType, method: str = "binning") -> CalibratorMapping:
        min_samples = getattr(self.settings, "CALIBRATION_MIN_RECORDS", 50)

        status = CalibrationStatus.PASS
        warnings = []
        if len(records) < min_samples:
            status = CalibrationStatus.INSUFFICIENT_DATA
            warnings.append(f"Insufficient samples for robust fitting: {len(records)} < {min_samples}. Falling back to identity mapping.")
            method = "identity"

        bin_mappings = {}
        if method == "binning":
            bins = self.bin_builder.build_bins(records, score_type, bin_size=10)
            for b in bins:
                if b.sample_count > 0 and b.observed_success_rate is not None:
                    bin_mappings[f"{b.lower_bound}-{b.upper_bound}"] = b.observed_success_rate * 100.0
                else:
                    avg_expected = (b.lower_bound + b.upper_bound) / 2.0
                    bin_mappings[f"{b.lower_bound}-{b.upper_bound}"] = avg_expected

        return CalibratorMapping(
            mapping_id=str(uuid.uuid4()),
            score_type=score_type,
            method=method,
            bin_mappings=bin_mappings,
            min_samples=min_samples,
            status=status,
            warnings=warnings
        )

    def calibrate_score(self, score: float, mapping: CalibratorMapping) -> float:
        if mapping.method == "identity" or mapping.status == CalibrationStatus.INSUFFICIENT_DATA or not mapping.bin_mappings:
            return float(max(0.0, min(100.0, score)))

        for key, calibrated in mapping.bin_mappings.items():
            try:
                parts = key.split('-')
                lower = float(parts[0])
                upper = float(parts[1])
                if lower <= score <= upper:
                    return float(max(0.0, min(100.0, calibrated)))
            except Exception:
                continue

        return float(max(0.0, min(100.0, score)))

    def apply_to_record(self, record: OutcomeRecord, mapping: CalibratorMapping) -> OutcomeRecord:
        val = mapping.score_type.value.lower()
        if val == 'signal_confidence':
            val = 'confidence_score'
        score = getattr(record, val, None)
        if score is not None:
            calibrated = self.calibrate_score(score, mapping)
            record.metadata["calibrated_confidence"] = calibrated
            record.metadata["calibration_mapping_id"] = mapping.mapping_id
        return record

    def evaluate(self, records: list[OutcomeRecord], score_type: CalibrationScoreType, horizon: OutcomeHorizon) -> CalibrationResult:
        bins = self.bin_builder.build_bins(records, score_type)
        metrics = self.metrics_calc.calculate_metrics(records, bins, score_type)
        curve = self.curve_builder.build_curve(records, score_type, horizon)

        status = curve.status
        warnings = curve.warnings.copy()

        strategy_name = records[0].strategy_name if records and all(r.strategy_name == records[0].strategy_name for r in records) else None
        symbol = records[0].symbol if records and all(r.symbol == records[0].symbol for r in records) else None

        return CalibrationResult(
            calibration_id=str(uuid.uuid4()),
            score_type=score_type,
            horizon=horizon,
            strategy_name=strategy_name,
            symbol=symbol,
            sample_count=len(records),
            bins=bins,
            metrics=metrics,
            reliability_curve=curve,
            status=status,
            warnings=warnings
        )

    def evaluate_all_score_types(self, records: list[OutcomeRecord], horizon: OutcomeHorizon) -> list[CalibrationResult]:
        results = []
        for score_type in CalibrationScoreType:
            if score_type == CalibrationScoreType.CUSTOM:
                continue
            has_scores = any(getattr(r, score_type.value.lower(), None) is not None for r in records)
            if has_scores:
                results.append(self.evaluate(records, score_type, horizon))
        return results
