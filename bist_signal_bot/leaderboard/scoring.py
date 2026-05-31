from bist_signal_bot.leaderboard.models import (
    ResearchCandidate, CandidateScore, SelectionPolicy, CandidateMetric, LeaderboardStatus, RankingMetricName
)
from bist_signal_bot.core.exceptions import LeaderboardScoringError

class CandidateScoringEngine:
    def __init__(self, settings=None):
        from bist_signal_bot.config.settings import get_settings
        self.settings = settings or get_settings()

    def score_candidate(self, candidate: ResearchCandidate, policy: SelectionPolicy | None = None) -> CandidateScore:
        score = CandidateScore(
            score_id=f"score_{candidate.candidate_id}",
            candidate_id=candidate.candidate_id,
            candidate_type=candidate.candidate_type
        )

        if policy is None:
            weights = {m.metric_name.value: m.weight for m in candidate.metrics}
        else:
            weights = policy.weights

        metric_scores = {}
        for m in candidate.metrics:
            norm_val = self.normalize_metric(m)
            metric_scores[m.metric_name.value] = norm_val

        score.metric_scores = metric_scores

        raw_score = self.weighted_raw_score(candidate.metrics, weights)
        score.raw_score = raw_score

        adjusted, penalties = self.apply_penalties(raw_score, candidate, policy)

        if adjusted is not None:
            adjusted = max(0.0, min(100.0, adjusted))

        score.adjusted_score = adjusted
        score.rank_score = adjusted
        score.penalties = penalties

        contributors_dict = self.contributors(candidate.metrics)
        score.positive_contributors = contributors_dict.get("positive", [])
        score.negative_contributors = contributors_dict.get("negative", [])

        score.status = self.status_from_score(adjusted, penalties, candidate)

        if score.status == LeaderboardStatus.BLOCKED_RESEARCH:
            score.warnings.append("BLOCKED_RESEARCH: Candidate is blocked by governance rules.")
            score.rank_score = -1.0 # Demote to bottom
        elif not candidate.metrics:
            score.status = LeaderboardStatus.INSUFFICIENT_DATA
            score.warnings.append("INSUFFICIENT_DATA: No metrics found.")

        return score

    def normalize_metric(self, metric: CandidateMetric) -> float | None:
        if metric.value is None:
            return None
        return metric.value

    def weighted_raw_score(self, metrics: list[CandidateMetric], weights: dict[str, float]) -> float | None:
        if not metrics:
            return None

        total_weight = 0.0
        score_sum = 0.0

        for m in metrics:
            w = weights.get(m.metric_name.value, 0.0)
            if w > 0 and m.value is not None:
                score_sum += m.value * w
                total_weight += w

        if total_weight == 0:
            return None

        return score_sum / total_weight

    def apply_penalties(self, raw_score: float | None, candidate: ResearchCandidate, policy: SelectionPolicy | None = None) -> tuple[float | None, dict[str, float]]:
        if raw_score is None:
            return None, {}

        penalties = {}
        adjusted = raw_score

        total_samples = 0
        samples_found = False
        for m in candidate.metrics:
            if m.sample_count is not None:
                total_samples = max(total_samples, m.sample_count)
                samples_found = True

        min_sample = policy.min_sample_count if policy else self.settings.LEADERBOARD_SELECTION_MIN_SAMPLE
        if samples_found and total_samples < min_sample:
            p_val = self.settings.LEADERBOARD_LOW_SAMPLE_PENALTY
            penalties["low_sample_penalty"] = p_val
            adjusted -= p_val

        has_leakage = any("leakage" in w.lower() for w in candidate.warnings)
        for m in candidate.metrics:
            if any("leakage" in w.lower() for w in m.warnings):
                has_leakage = True

        if has_leakage:
            p_val = self.settings.LEADERBOARD_LEAKAGE_PENALTY
            penalties["leakage_penalty"] = p_val
            adjusted -= p_val

            if policy and policy.block_on_leakage:
                penalties["leakage_block"] = 100.0
                adjusted = 0.0

        return adjusted, penalties

    def contributors(self, metrics: list[CandidateMetric]) -> dict[str, list[str]]:
        positive = []
        negative = []
        for m in metrics:
            if m.value is not None:
                if m.value > 75.0:
                    positive.append(m.metric_name.value)
                elif m.value < 40.0:
                    negative.append(m.metric_name.value)
        return {"positive": positive, "negative": negative}

    def status_from_score(self, score: float | None, penalties: dict[str, float], candidate: ResearchCandidate) -> LeaderboardStatus:
        if "leakage_block" in penalties:
            return LeaderboardStatus.BLOCKED_RESEARCH

        if score is None:
            return LeaderboardStatus.UNKNOWN

        if score >= self.settings.LEADERBOARD_SCORE_PASS_THRESHOLD:
            return LeaderboardStatus.PASS
        elif score >= self.settings.LEADERBOARD_SCORE_WATCH_THRESHOLD:
            return LeaderboardStatus.WATCH
        elif score >= self.settings.LEADERBOARD_SCORE_FAIL_THRESHOLD:
            return LeaderboardStatus.DEGRADED
        else:
            return LeaderboardStatus.FAIL
