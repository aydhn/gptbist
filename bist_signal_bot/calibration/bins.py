import uuid
import math
from bist_signal_bot.calibration.models import (
    OutcomeRecord, CalibrationBin, CalibrationScoreType, OutcomeLabel, CalibrationStatus
)
from bist_signal_bot.config.settings import Settings

class CalibrationBinBuilder:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def _get_score(self, record: OutcomeRecord, score_type: CalibrationScoreType) -> float | None:
        val = score_type.value.lower()
        if val == 'signal_confidence':
            val = 'confidence_score'
        return getattr(record, val, None)

    def build_bins(self, records: list[OutcomeRecord], score_type: CalibrationScoreType, bin_size: int = 10) -> list[CalibrationBin]:
        bins_data = {}

        num_bins = math.ceil(100.0 / bin_size)
        for i in range(num_bins):
            lower = float(i * bin_size)
            upper = float((i + 1) * bin_size)
            bins_data[(lower, upper)] = []

        for record in records:
            if record.outcome_label == OutcomeLabel.NOT_EVALUATED:
                continue

            score = self._get_score(record, score_type)
            if score is None:
                continue

            lower, upper = self.assign_bin(score, bin_size)
            if (lower, upper) in bins_data:
                bins_data[(lower, upper)].append(record)

        result_bins = []
        for (lower, upper), bin_records in bins_data.items():
            result_bins.append(self.summarize_bin(bin_records, score_type, lower, upper))

        if getattr(self.settings, "CALIBRATION_MERGE_SPARSE_BINS", True):
            min_samples = getattr(self.settings, "CALIBRATION_MIN_BIN_SAMPLES", 10)
            result_bins = self.merge_sparse_bins(result_bins, min_samples)

        return result_bins

    def assign_bin(self, score: float, bin_size: int = 10) -> tuple[float, float]:
        if score >= 100.0:
            upper = 100.0
            lower = float(100 - bin_size)
            return (lower, upper)

        bin_idx = int(score // bin_size)
        lower = float(bin_idx * bin_size)
        upper = float((bin_idx + 1) * bin_size)
        return (lower, upper)

    def summarize_bin(self, records: list[OutcomeRecord], score_type: CalibrationScoreType, lower: float, upper: float) -> CalibrationBin:
        sample_count = len(records)
        success_count = sum(1 for r in records if r.outcome_label == OutcomeLabel.SUCCESS)
        failure_count = sum(1 for r in records if r.outcome_label == OutcomeLabel.FAILURE)
        neutral_count = sample_count - success_count - failure_count

        avg_score = None
        if sample_count > 0:
            scores = [self._get_score(r, score_type) for r in records if self._get_score(r, score_type) is not None]
            if scores:
                avg_score = sum(scores) / len(scores)

        obs_rate = success_count / sample_count if sample_count > 0 else None
        gap = None
        if avg_score is not None and obs_rate is not None:
            gap = obs_rate - (avg_score / 100.0)

        gross_returns = [r.gross_return_pct for r in records if r.gross_return_pct is not None]
        avg_gross = sum(gross_returns) / len(gross_returns) if gross_returns else None

        net_returns = [r.net_return_pct for r in records if r.net_return_pct is not None]
        avg_net = sum(net_returns) / len(net_returns) if net_returns else None

        cost_drags = [r.cost_drag_pct for r in records if r.cost_drag_pct is not None]
        avg_cost = sum(cost_drags) / len(cost_drags) if cost_drags else None

        status = CalibrationStatus.UNKNOWN
        warnings = []
        if sample_count < getattr(self.settings, "CALIBRATION_MIN_BIN_SAMPLES", 10):
            status = CalibrationStatus.INSUFFICIENT_DATA
            warnings.append(f"Sparse bin: {sample_count} samples")

        return CalibrationBin(
            bin_id=str(uuid.uuid4()),
            score_type=score_type,
            lower_bound=lower,
            upper_bound=upper,
            sample_count=sample_count,
            success_count=success_count,
            failure_count=failure_count,
            neutral_count=neutral_count,
            average_score=avg_score,
            observed_success_rate=obs_rate,
            average_gross_return_pct=avg_gross,
            average_net_return_pct=avg_net,
            average_cost_drag_pct=avg_cost,
            calibration_gap=gap,
            status=status,
            warnings=warnings
        )

    def merge_sparse_bins(self, bins: list[CalibrationBin], min_samples: int) -> list[CalibrationBin]:
        if not bins:
            return []

        bins.sort(key=lambda b: b.lower_bound)

        merged = []
        current = None

        for b in bins:
            if current is None:
                current = b
            else:
                if current.sample_count < min_samples:
                    total_samples = current.sample_count + b.sample_count

                    if total_samples > 0:
                        if current.average_score is not None and b.average_score is not None:
                            avg_score = ((current.average_score * current.sample_count) + (b.average_score * b.sample_count)) / total_samples
                        else:
                            avg_score = current.average_score or b.average_score

                        success = current.success_count + b.success_count
                        obs_rate = success / total_samples

                        gap = None
                        if avg_score is not None and obs_rate is not None:
                            gap = obs_rate - (avg_score / 100.0)
                    else:
                        avg_score = None
                        obs_rate = None
                        gap = None

                    current = CalibrationBin(
                        bin_id=str(uuid.uuid4()),
                        score_type=current.score_type,
                        lower_bound=current.lower_bound,
                        upper_bound=b.upper_bound,
                        sample_count=total_samples,
                        success_count=current.success_count + b.success_count,
                        failure_count=current.failure_count + b.failure_count,
                        neutral_count=current.neutral_count + b.neutral_count,
                        average_score=avg_score,
                        observed_success_rate=obs_rate,
                        calibration_gap=gap,
                        status=CalibrationStatus.UNKNOWN if total_samples >= min_samples else CalibrationStatus.INSUFFICIENT_DATA,
                        warnings=[] if total_samples >= min_samples else [f"Sparse merged bin: {total_samples} samples"]
                    )
                else:
                    merged.append(current)
                    current = b

        if current:
            merged.append(current)

        if len(merged) > 1 and merged[-1].sample_count < min_samples:
            last = merged.pop()
            prev = merged.pop()
            prev.upper_bound = last.upper_bound
            prev.sample_count += last.sample_count
            prev.success_count += last.success_count
            prev.failure_count += last.failure_count
            prev.neutral_count += last.neutral_count
            merged.append(prev)

        return merged
