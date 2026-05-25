import uuid
import math
from bist_signal_bot.calibration.models import (
    OutcomeRecord, CalibrationBin, CalibrationScoreType, CalibrationMetricType, CalibrationMetric, CalibrationStatus, OutcomeLabel
)
from bist_signal_bot.config.settings import Settings

class CalibrationMetricsCalculator:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def _get_score(self, record: OutcomeRecord, score_type: CalibrationScoreType) -> float | None:
        val = score_type.value.lower()
        if val == 'signal_confidence':
            val = 'confidence_score'
        return getattr(record, val, None)

    def calculate_metrics(self, records: list[OutcomeRecord], bins: list[CalibrationBin], score_type: CalibrationScoreType) -> list[CalibrationMetric]:
        metrics = []

        brier = self.brier_score(records, score_type)
        if brier is not None:
            metrics.append(CalibrationMetric(
                metric_id=str(uuid.uuid4()),
                metric_type=CalibrationMetricType.BRIER_SCORE,
                score_type=score_type,
                name="Brier Score",
                value=brier,
                status=CalibrationStatus.PASS if brier < 0.25 else CalibrationStatus.WATCH
            ))

        ece = self.expected_calibration_error(bins)
        if ece is not None:
            status = CalibrationStatus.PASS
            warn = getattr(self.settings, "CALIBRATION_ECE_WARN", 0.10)
            fail = getattr(self.settings, "CALIBRATION_ECE_FAIL", 0.20)
            if ece > fail:
                status = CalibrationStatus.FAIL
            elif ece > warn:
                status = CalibrationStatus.WATCH

            metrics.append(CalibrationMetric(
                metric_id=str(uuid.uuid4()),
                metric_type=CalibrationMetricType.EXPECTED_CALIBRATION_ERROR,
                score_type=score_type,
                name="Expected Calibration Error",
                value=ece,
                status=status,
                threshold_warn=warn,
                threshold_fail=fail
            ))

        mce = self.max_calibration_error(bins)
        if mce is not None:
            status = CalibrationStatus.PASS
            warn = getattr(self.settings, "CALIBRATION_MCE_WARN", 0.20)
            fail = getattr(self.settings, "CALIBRATION_MCE_FAIL", 0.35)
            if mce > fail:
                status = CalibrationStatus.FAIL
            elif mce > warn:
                status = CalibrationStatus.WATCH

            metrics.append(CalibrationMetric(
                metric_id=str(uuid.uuid4()),
                metric_type=CalibrationMetricType.MAX_CALIBRATION_ERROR,
                score_type=score_type,
                name="Max Calibration Error",
                value=mce,
                status=status,
                threshold_warn=warn,
                threshold_fail=fail
            ))

        hit_r = self.hit_rate(records)
        if hit_r is not None:
            metrics.append(CalibrationMetric(
                metric_id=str(uuid.uuid4()),
                metric_type=CalibrationMetricType.HIT_RATE,
                score_type=score_type,
                name="Hit Rate",
                value=hit_r,
                status=CalibrationStatus.PASS if hit_r > 0.5 else CalibrationStatus.WATCH
            ))

        return metrics

    def brier_score(self, records: list[OutcomeRecord], score_type: CalibrationScoreType) -> float | None:
        valid_records = []
        for r in records:
            score = self._get_score(r, score_type)
            if score is not None and r.outcome_label in [OutcomeLabel.SUCCESS, OutcomeLabel.FAILURE]:
                valid_records.append((score / 100.0, 1.0 if r.outcome_label == OutcomeLabel.SUCCESS else 0.0))

        if not valid_records:
            return None

        brier = sum((score - outcome) ** 2 for score, outcome in valid_records) / len(valid_records)
        return brier

    def expected_calibration_error(self, bins: list[CalibrationBin]) -> float | None:
        total_samples = sum(b.sample_count for b in bins)
        if total_samples == 0:
            return None

        ece = 0.0
        for b in bins:
            if b.sample_count > 0 and b.calibration_gap is not None:
                weight = b.sample_count / total_samples
                ece += weight * abs(b.calibration_gap)

        return ece

    def max_calibration_error(self, bins: list[CalibrationBin]) -> float | None:
        gaps = [abs(b.calibration_gap) for b in bins if b.sample_count > 0 and b.calibration_gap is not None]
        if not gaps:
            return None
        return max(gaps)

    def hit_rate(self, records: list[OutcomeRecord]) -> float | None:
        valid = [r for r in records if r.outcome_label in [OutcomeLabel.SUCCESS, OutcomeLabel.FAILURE]]
        if not valid:
            return None
        success = sum(1 for r in valid if r.outcome_label == OutcomeLabel.SUCCESS)
        return success / len(valid)

    def false_positive_rate(self, records: list[OutcomeRecord], score_type: CalibrationScoreType, threshold: float) -> float | None:
        valid = [r for r in records if r.outcome_label in [OutcomeLabel.SUCCESS, OutcomeLabel.FAILURE]]
        negatives = [r for r in valid if r.outcome_label == OutcomeLabel.FAILURE]
        if not negatives:
            return None

        false_positives = sum(1 for r in negatives if (self._get_score(r, score_type) or 0) >= threshold)
        return false_positives / len(negatives)

    def precision_recall_f1(self, records: list[OutcomeRecord], score_type: CalibrationScoreType, threshold: float) -> dict[str, float | None]:
        valid = [r for r in records if r.outcome_label in [OutcomeLabel.SUCCESS, OutcomeLabel.FAILURE]]
        if not valid:
            return {"precision": None, "recall": None, "f1": None}

        tp = sum(1 for r in valid if r.outcome_label == OutcomeLabel.SUCCESS and (self._get_score(r, score_type) or 0) >= threshold)
        fp = sum(1 for r in valid if r.outcome_label == OutcomeLabel.FAILURE and (self._get_score(r, score_type) or 0) >= threshold)
        fn = sum(1 for r in valid if r.outcome_label == OutcomeLabel.SUCCESS and (self._get_score(r, score_type) or 0) < threshold)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {"precision": precision, "recall": recall, "f1": f1}

    def auc_lite(self, records: list[OutcomeRecord], score_type: CalibrationScoreType) -> float | None:
        valid = [r for r in records if r.outcome_label in [OutcomeLabel.SUCCESS, OutcomeLabel.FAILURE]]
        successes = [r for r in valid if r.outcome_label == OutcomeLabel.SUCCESS]
        failures = [r for r in valid if r.outcome_label == OutcomeLabel.FAILURE]

        if not successes or not failures:
            return None

        concordant = 0
        discordant = 0
        ties = 0

        for s in successes:
            s_score = self._get_score(s, score_type) or 0
            for f in failures:
                f_score = self._get_score(f, score_type) or 0
                if s_score > f_score:
                    concordant += 1
                elif s_score < f_score:
                    discordant += 1
                else:
                    ties += 1

        total_pairs = len(successes) * len(failures)
        auc = (concordant + 0.5 * ties) / total_pairs
        return auc
