import uuid
from bist_signal_bot.calibration.models import (
    OutcomeRecord, ReliabilityCurve, CalibrationScoreType, OutcomeHorizon, CalibrationStatus, CalibrationMetricType
)
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.calibration.bins import CalibrationBinBuilder
from bist_signal_bot.calibration.metrics import CalibrationMetricsCalculator

class ReliabilityCurveBuilder:
    def __init__(self, settings: Settings | None = None, bin_builder: CalibrationBinBuilder | None = None, metrics_calc: CalibrationMetricsCalculator | None = None):
        self.settings = settings or Settings()
        self.bin_builder = bin_builder or CalibrationBinBuilder(self.settings)
        self.metrics_calc = metrics_calc or CalibrationMetricsCalculator(self.settings)

    def build_curve(self, records: list[OutcomeRecord], score_type: CalibrationScoreType, horizon: OutcomeHorizon, bin_size: int = 10, min_bin_samples: int = 10) -> ReliabilityCurve:
        bins = self.bin_builder.build_bins(records, score_type, bin_size=bin_size)

        ece = self.metrics_calc.expected_calibration_error(bins)
        mce = self.metrics_calc.max_calibration_error(bins)

        sample_count = sum(b.sample_count for b in bins)

        curve = ReliabilityCurve(
            curve_id=str(uuid.uuid4()),
            score_type=score_type,
            horizon=horizon,
            bins=bins,
            expected_calibration_error=ece,
            max_calibration_error=mce,
            sample_count=sample_count
        )

        curve.status = self.classify_curve(curve)
        curve.warnings = self.curve_findings(curve)

        return curve

    def classify_curve(self, curve: ReliabilityCurve) -> CalibrationStatus:
        if curve.sample_count < getattr(self.settings, "CALIBRATION_MIN_RECORDS", 50):
            return CalibrationStatus.INSUFFICIENT_DATA

        fail_ece = getattr(self.settings, "CALIBRATION_ECE_FAIL", 0.20)
        warn_ece = getattr(self.settings, "CALIBRATION_ECE_WARN", 0.10)

        if curve.expected_calibration_error is not None:
            if curve.expected_calibration_error > fail_ece:
                return CalibrationStatus.FAIL
            elif curve.expected_calibration_error > warn_ece:
                return CalibrationStatus.WATCH

        high_bins = [b for b in curve.bins if b.lower_bound >= 70.0 and b.sample_count > 0]
        for b in high_bins:
            if b.observed_success_rate is not None and b.average_score is not None:
                if b.observed_success_rate < 0.4 and b.average_score > 75.0:
                    return CalibrationStatus.FAIL
                elif b.observed_success_rate < 0.5 and b.average_score > 70.0:
                    return CalibrationStatus.WATCH

        return CalibrationStatus.PASS

    def curve_findings(self, curve: ReliabilityCurve) -> list[str]:
        findings = []
        if curve.sample_count < getattr(self.settings, "CALIBRATION_MIN_RECORDS", 50):
            findings.append(f"Curve relies on small sample size ({curve.sample_count} records).")

        high_bins = [b for b in curve.bins if b.lower_bound >= 70.0 and b.sample_count > 0]
        for b in high_bins:
            if b.observed_success_rate is not None and b.average_score is not None:
                if b.observed_success_rate < 0.5:
                    findings.append(f"High confidence bin ({b.lower_bound}-{b.upper_bound}) underperforms with {b.observed_success_rate:.1%} success rate.")
                elif b.calibration_gap is not None and b.calibration_gap < -0.2:
                    findings.append(f"High confidence bin ({b.lower_bound}-{b.upper_bound}) is significantly overconfident (gap: {b.calibration_gap:.2f}).")

        return findings
