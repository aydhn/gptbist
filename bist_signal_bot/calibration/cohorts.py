import uuid
from bist_signal_bot.calibration.models import (
    OutcomeRecord, CalibrationScoreType, OutcomeCohort, CalibrationStatus, OutcomeLabel
)
from bist_signal_bot.config.settings import Settings

class OutcomeCohortAnalyzer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def analyze_cohorts(self, records: list[OutcomeRecord], score_type: CalibrationScoreType) -> list[OutcomeCohort]:
        cohorts = []

        cohorts.extend(self.cohort_by_field(records, "strategy_name", score_type))
        cohorts.extend(self.cohort_by_field(records, "symbol", score_type))
        cohorts.extend(self.cohort_by_field(records, "sector", score_type))
        cohorts.extend(self.cohort_by_field(records, "regime_label", score_type))
        cohorts.extend(self.cohort_by_field(records, "liquidity_status", score_type))

        return cohorts

    def cohort_by_field(self, records: list[OutcomeRecord], field_name: str, score_type: CalibrationScoreType) -> list[OutcomeCohort]:
        groups = {}
        for r in records:
            if r.outcome_label == OutcomeLabel.NOT_EVALUATED:
                continue
            val = getattr(r, field_name, None)
            if val is not None:
                groups.setdefault(val, []).append(r)

        cohorts = []
        for val, group_records in groups.items():
            cohorts.append(self.build_cohort(group_records, f"{field_name}:{val}", {field_name: val}, score_type))

        return cohorts

    def build_cohort(self, records: list[OutcomeRecord], name: str, filters: dict, score_type: CalibrationScoreType) -> OutcomeCohort:
        sample_count = len(records)

        success_count = sum(1 for r in records if r.outcome_label == OutcomeLabel.SUCCESS)
        success_rate = success_count / sample_count if sample_count > 0 else None

        net_returns = [r.net_return_pct for r in records if r.net_return_pct is not None]
        avg_net = sum(net_returns) / len(net_returns) if net_returns else None

        scores = [getattr(r, 'confidence_score' if score_type.value.lower() == 'signal_confidence' else score_type.value.lower(), None) for r in records if getattr(r, 'confidence_score' if score_type.value.lower() == 'signal_confidence' else score_type.value.lower(), None) is not None]
        avg_score = sum(scores) / len(scores) if scores else None

        gap = None
        if success_rate is not None and avg_score is not None:
            gap = success_rate - (avg_score / 100.0)

        status = CalibrationStatus.UNKNOWN
        warnings = []
        min_samples = getattr(self.settings, "CALIBRATION_MIN_COHORT_SAMPLES", 20)

        if sample_count < min_samples:
            status = CalibrationStatus.INSUFFICIENT_DATA
            warnings.append(f"Small cohort size: {sample_count} < {min_samples}")
        elif success_rate is not None and success_rate < 0.4:
            status = CalibrationStatus.FAIL
        elif gap is not None and gap < -0.2:
            status = CalibrationStatus.FAIL
        else:
            status = CalibrationStatus.PASS

        return OutcomeCohort(
            cohort_id=str(uuid.uuid4()),
            name=name,
            filters=filters,
            sample_count=sample_count,
            success_rate=success_rate,
            average_net_return_pct=avg_net,
            average_score=avg_score,
            calibration_gap=gap,
            status=status,
            warnings=warnings
        )

    def detect_weak_cohorts(self, cohorts: list[OutcomeCohort]) -> list[OutcomeCohort]:
        return [c for c in cohorts if c.status in [CalibrationStatus.FAIL, CalibrationStatus.WATCH] and c.sample_count >= getattr(self.settings, "CALIBRATION_MIN_COHORT_SAMPLES", 20)]
