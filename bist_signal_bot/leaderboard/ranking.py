from datetime import datetime
from bist_signal_bot.leaderboard.models import (
    BenchmarkCohort, ResearchLeaderboard, SelectionPolicy, ResearchCandidate,
    CandidateScore, LeaderboardEntry, CandidateDecision, LeaderboardStatus
)
from bist_signal_bot.core.exceptions import CandidateRankingError
import hashlib

class CandidateRankingEngine:
    def __init__(self, scoring_engine=None, settings=None):
        from bist_signal_bot.leaderboard.scoring import CandidateScoringEngine
        from bist_signal_bot.config.settings import get_settings
        self.settings = settings or get_settings()
        self.scoring_engine = scoring_engine or CandidateScoringEngine(self.settings)

    def build_leaderboard(self, cohort: BenchmarkCohort, candidates: list[ResearchCandidate], policy: SelectionPolicy | None = None) -> ResearchLeaderboard:
        lb = ResearchLeaderboard(
            leaderboard_id=f"lb_{cohort.cohort_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            cohort_id=cohort.cohort_id
        )

        scores = []
        for c in candidates:
            score = self.scoring_engine.score_candidate(c, policy)
            scores.append(score)

        entries = self.rank_candidates(candidates, scores, policy)
        lb.entries = entries

        if entries:
            top_entry = entries[0]
            if top_entry.score.status != LeaderboardStatus.BLOCKED_RESEARCH and top_entry.score.rank_score and top_entry.score.rank_score >= self.settings.LEADERBOARD_SCORE_PASS_THRESHOLD:
                lb.top_candidate_id = top_entry.candidate.candidate_id

            lb.watch_count = sum(1 for e in entries if e.score.status in (LeaderboardStatus.WATCH, LeaderboardStatus.DEGRADED))
            lb.blocked_count = sum(1 for e in entries if e.score.status == LeaderboardStatus.BLOCKED_RESEARCH)

        lb.status = self.leaderboard_status(entries)
        return lb

    def rank_candidates(self, candidates: list[ResearchCandidate], scores: list[CandidateScore], policy: SelectionPolicy | None = None) -> list[LeaderboardEntry]:
        entries = []
        c_map = {c.candidate_id: c for c in candidates}

        for score in scores:
            c = c_map.get(score.candidate_id)
            if not c:
                continue

            entry = LeaderboardEntry(
                entry_id=f"entry_{c.candidate_id}",
                leaderboard_id="",
                candidate=c,
                score=score
            )
            entries.append(entry)

        entries.sort(key=lambda e: (
            e.score.rank_score if e.score.rank_score is not None else -100.0,
            int(hashlib.md5(e.candidate.candidate_id.encode()).hexdigest(), 16)
        ), reverse=True)

        for i, entry in enumerate(entries):
            entry.rank = i + 1
            entry.decision = self.decision_for_entry(entry.candidate, entry.score, entry.rank, policy)
            entry.review_required = self.review_required(entry.candidate, entry.score, entry.decision)
            entry.key_reasons = self.key_reasons(entry.candidate, entry.score, entry.decision)

        return entries

    def decision_for_entry(self, candidate: ResearchCandidate, score: CandidateScore, rank: int | None, policy: SelectionPolicy | None = None) -> CandidateDecision:
        if score.status == LeaderboardStatus.BLOCKED_RESEARCH:
            return CandidateDecision.BLOCKED_RESEARCH

        if score.status == LeaderboardStatus.INSUFFICIENT_DATA:
            return CandidateDecision.NEEDS_MORE_DATA

        if rank == 1 and score.status == LeaderboardStatus.PASS:
            return CandidateDecision.TOP_RESEARCH_CANDIDATE

        if score.status in (LeaderboardStatus.WATCH, LeaderboardStatus.DEGRADED, LeaderboardStatus.PASS):
            return CandidateDecision.WATCH_RESEARCH_CANDIDATE

        return CandidateDecision.REJECT_RESEARCH_CANDIDATE

    def review_required(self, candidate: ResearchCandidate, score: CandidateScore, decision: CandidateDecision) -> bool:
        if decision == CandidateDecision.BLOCKED_RESEARCH:
            return True
        if decision == CandidateDecision.TOP_RESEARCH_CANDIDATE and score.status != LeaderboardStatus.PASS:
            return True
        return False

    def key_reasons(self, candidate: ResearchCandidate, score: CandidateScore, decision: CandidateDecision) -> list[str]:
        reasons = []
        if score.status == LeaderboardStatus.BLOCKED_RESEARCH:
            reasons.append("Candidate is blocked due to governance or leakage penalties.")
        if score.rank_score is not None:
            reasons.append(f"Rank Score: {score.rank_score:.2f}")
        for p in score.penalties:
            reasons.append(f"Penalty: {p}")
        return reasons

    def leaderboard_status(self, entries: list[LeaderboardEntry]) -> LeaderboardStatus:
        if not entries:
            return LeaderboardStatus.INSUFFICIENT_DATA
        if any(e.score.status == LeaderboardStatus.BLOCKED_RESEARCH for e in entries):
            return LeaderboardStatus.DEGRADED
        if entries[0].score.status == LeaderboardStatus.PASS:
            return LeaderboardStatus.PASS
        return LeaderboardStatus.WATCH
