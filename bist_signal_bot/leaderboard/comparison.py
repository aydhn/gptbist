from datetime import datetime
from bist_signal_bot.leaderboard.models import (
    ResearchCandidate, CandidateComparison, CandidateDecision, SelectionPolicy, RankingMetricName
)

class CandidateComparisonEngine:
    def __init__(self, scoring_engine=None, settings=None):
        from bist_signal_bot.leaderboard.scoring import CandidateScoringEngine
        from bist_signal_bot.config.settings import get_settings
        self.settings = settings or get_settings()
        self.scoring_engine = scoring_engine or CandidateScoringEngine(self.settings)

    def compare(self, candidate_a: ResearchCandidate, candidate_b: ResearchCandidate, policy: SelectionPolicy | None = None) -> CandidateComparison:
        comp = CandidateComparison(
            comparison_id=f"comp_{candidate_a.candidate_id}_{candidate_b.candidate_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            candidate_a_id=candidate_a.candidate_id,
            candidate_b_id=candidate_b.candidate_id,
            candidate_type=candidate_a.candidate_type
        )

        comp.metric_deltas = self.metric_deltas(candidate_a, candidate_b)
        comp.winner_candidate_id = self.winner(candidate_a, candidate_b, policy)
        comp.reasons = self.comparison_reasons(candidate_a, candidate_b)
        comp.decision = self.decision_from_comparison(comp.winner_candidate_id, comp.metric_deltas)

        return comp

    def metric_deltas(self, candidate_a: ResearchCandidate, candidate_b: ResearchCandidate) -> dict[str, float | None]:
        deltas = {}
        a_metrics = {m.metric_name.value: m for m in candidate_a.metrics}
        b_metrics = {m.metric_name.value: m for m in candidate_b.metrics}

        all_keys = set(a_metrics.keys()).union(b_metrics.keys())
        for k in all_keys:
            a_val = a_metrics[k].value if k in a_metrics else None
            b_val = b_metrics[k].value if k in b_metrics else None

            if a_val is not None and b_val is not None:
                deltas[k] = a_val - b_val
            else:
                deltas[k] = None

        return deltas

    def winner(self, candidate_a: ResearchCandidate, candidate_b: ResearchCandidate, policy: SelectionPolicy | None = None) -> str | None:
        score_a = self.scoring_engine.score_candidate(candidate_a, policy)
        score_b = self.scoring_engine.score_candidate(candidate_b, policy)

        if score_a.rank_score is None and score_b.rank_score is None:
            return None
        if score_a.rank_score is None:
            return candidate_b.candidate_id
        if score_b.rank_score is None:
            return candidate_a.candidate_id

        if score_a.rank_score > score_b.rank_score:
            return candidate_a.candidate_id
        elif score_b.rank_score > score_a.rank_score:
            return candidate_b.candidate_id

        return None

    def comparison_reasons(self, candidate_a: ResearchCandidate, candidate_b: ResearchCandidate) -> list[str]:
        return ["Comparison relies on computed rank scores.", "This is research metadata only."]

    def decision_from_comparison(self, winner_id: str | None, deltas: dict[str, float | None]) -> CandidateDecision:
        if not deltas:
            return CandidateDecision.NEEDS_MORE_DATA
        if winner_id is None:
            return CandidateDecision.WATCH_RESEARCH_CANDIDATE
        return CandidateDecision.WATCH_RESEARCH_CANDIDATE
