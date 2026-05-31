import pytest
from bist_signal_bot.leaderboard.ranking import CandidateRankingEngine
from bist_signal_bot.leaderboard.models import ResearchCandidate, CandidateType, CandidateScore, LeaderboardStatus
from bist_signal_bot.config.settings import Settings

def test_ranking_deterministic_sort():
    engine = CandidateRankingEngine(settings=Settings())
    c1 = ResearchCandidate(candidate_id="c1", candidate_type=CandidateType.STRATEGY, name="C1")
    c2 = ResearchCandidate(candidate_id="c2", candidate_type=CandidateType.STRATEGY, name="C2")
    s1 = CandidateScore(score_id="s1", candidate_id="c1", candidate_type=CandidateType.STRATEGY, rank_score=80.0)
    s2 = CandidateScore(score_id="s2", candidate_id="c2", candidate_type=CandidateType.STRATEGY, rank_score=80.0)
    entries1 = engine.rank_candidates([c1, c2], [s1, s2])
    entries2 = engine.rank_candidates([c2, c1], [s2, s1])
    assert entries1[0].candidate.candidate_id == entries2[0].candidate.candidate_id

def test_ranking_blocked_candidate_not_top():
    engine = CandidateRankingEngine(settings=Settings())
    c1 = ResearchCandidate(candidate_id="c1", candidate_type=CandidateType.STRATEGY, name="C1")
    c2 = ResearchCandidate(candidate_id="c2", candidate_type=CandidateType.STRATEGY, name="C2")
    s1 = CandidateScore(score_id="s1", candidate_id="c1", candidate_type=CandidateType.STRATEGY, rank_score=-1.0, status=LeaderboardStatus.BLOCKED_RESEARCH)
    s2 = CandidateScore(score_id="s2", candidate_id="c2", candidate_type=CandidateType.STRATEGY, rank_score=50.0, status=LeaderboardStatus.FAIL)
    entries = engine.rank_candidates([c1, c2], [s1, s2])
    assert entries[0].candidate.candidate_id == "c2"

def test_ranking_review_required():
    engine = CandidateRankingEngine(settings=Settings())
    c1 = ResearchCandidate(candidate_id="c1", candidate_type=CandidateType.STRATEGY, name="C1")
    s1 = CandidateScore(score_id="s1", candidate_id="c1", candidate_type=CandidateType.STRATEGY, rank_score=-1.0, status=LeaderboardStatus.BLOCKED_RESEARCH)
    entries = engine.rank_candidates([c1], [s1])
    assert entries[0].review_required is True
