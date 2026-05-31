from bist_signal_bot.leaderboard.models import (
    ResearchCandidate, CandidateType, CandidateMetric, RankingMetricName, LeaderboardStatus
)
from bist_signal_bot.core.exceptions import LeaderboardCollectorError

class LeaderboardDataCollector:
    def __init__(self, settings=None):
        from bist_signal_bot.config.settings import get_settings
        self.settings = settings or get_settings()

    def collect_candidate(self, candidate_type: CandidateType, candidate_id: str) -> ResearchCandidate:
        if candidate_type == CandidateType.STRATEGY:
            return self.collect_strategy_candidate(candidate_id)
        elif candidate_type == CandidateType.MODEL:
            return self.collect_model_candidate(candidate_id)
        elif candidate_type == CandidateType.FEATURE_SET:
            return self.collect_feature_set_candidate(candidate_id)
        else:
            candidate = ResearchCandidate(
                candidate_id=candidate_id,
                candidate_type=candidate_type,
                name=f"{candidate_type.value} {candidate_id}",
                warnings=[f"Missing source: unsupported type {candidate_type}"]
            )
            return candidate

    def collect_strategy_candidate(self, strategy_name: str) -> ResearchCandidate:
        candidate = ResearchCandidate(
            candidate_id=strategy_name,
            candidate_type=CandidateType.STRATEGY,
            name=strategy_name
        )
        candidate.metrics = self.collect_metrics(candidate)
        return candidate

    def collect_model_candidate(self, model_id: str) -> ResearchCandidate:
        candidate = ResearchCandidate(
            candidate_id=model_id,
            candidate_type=CandidateType.MODEL,
            name=model_id
        )
        candidate.metrics = self.collect_metrics(candidate)
        return candidate

    def collect_feature_set_candidate(self, feature_set_id: str) -> ResearchCandidate:
        candidate = ResearchCandidate(
            candidate_id=feature_set_id,
            candidate_type=CandidateType.FEATURE_SET,
            name=feature_set_id
        )
        candidate.metrics = self.collect_metrics(candidate)
        return candidate

    def collect_metrics(self, candidate: ResearchCandidate) -> list[CandidateMetric]:
        metrics = []
        m_val = self.collect_validation_metric(candidate)
        if m_val: metrics.append(m_val)
        m_cal = self.collect_calibration_metric(candidate)
        if m_cal: metrics.append(m_cal)
        m_mon = self.collect_monitoring_metric(candidate)
        if m_mon: metrics.append(m_mon)
        m_fq = self.collect_feature_quality_metric(candidate)
        if m_fq: metrics.append(m_fq)
        m_gov = self.collect_model_governance_metric(candidate)
        if m_gov: metrics.append(m_gov)
        m_ctx = self.collect_context_support_metric(candidate)
        if m_ctx: metrics.append(m_ctx)
        m_rev = self.collect_review_burden_metric(candidate)
        if m_rev: metrics.append(m_rev)
        m_dq = self.collect_data_quality_metric(candidate)
        if m_dq: metrics.append(m_dq)
        return metrics

    def _mock_metric(self, candidate: ResearchCandidate, name: RankingMetricName) -> CandidateMetric:
        return CandidateMetric(
            metric_id=f"{candidate.candidate_id}_{name.value}",
            candidate_type=candidate.candidate_type,
            candidate_id=candidate.candidate_id,
            metric_name=name,
            warnings=["Missing source"]
        )

    def collect_validation_metric(self, candidate: ResearchCandidate) -> CandidateMetric | None:
        return self._mock_metric(candidate, RankingMetricName.VALIDATION_SCORE)

    def collect_calibration_metric(self, candidate: ResearchCandidate) -> CandidateMetric | None:
        return self._mock_metric(candidate, RankingMetricName.CALIBRATION_SCORE)

    def collect_monitoring_metric(self, candidate: ResearchCandidate) -> CandidateMetric | None:
        return self._mock_metric(candidate, RankingMetricName.MONITORING_HEALTH)

    def collect_feature_quality_metric(self, candidate: ResearchCandidate) -> CandidateMetric | None:
        return self._mock_metric(candidate, RankingMetricName.FEATURE_QUALITY)

    def collect_model_governance_metric(self, candidate: ResearchCandidate) -> CandidateMetric | None:
        return self._mock_metric(candidate, RankingMetricName.MODEL_GOVERNANCE)

    def collect_context_support_metric(self, candidate: ResearchCandidate) -> CandidateMetric | None:
        return self._mock_metric(candidate, RankingMetricName.CONTEXT_SUPPORT)

    def collect_review_burden_metric(self, candidate: ResearchCandidate) -> CandidateMetric | None:
        return self._mock_metric(candidate, RankingMetricName.REVIEW_BURDEN)

    def collect_data_quality_metric(self, candidate: ResearchCandidate) -> CandidateMetric | None:
        return self._mock_metric(candidate, RankingMetricName.DATA_QUALITY)
