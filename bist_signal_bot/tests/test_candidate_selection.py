import pytest
from bist_signal_bot.leaderboard.selection import CandidateSelectionEngine
from bist_signal_bot.leaderboard.models import ResearchLeaderboard, LeaderboardEntry, ResearchCandidate, CandidateType, CandidateScore, LeaderboardStatus
from bist_signal_bot.config.settings import Settings

def test_selection_blocked_candidate():
    engine = CandidateSelectionEngine(settings=Settings())
    c1 = ResearchCandidate(candidate_id="c1", candidate_type=CandidateType.STRATEGY, name="C1")
    s1 = CandidateScore(score_id="s1", candidate_id="c1", candidate_type=CandidateType.STRATEGY, status=LeaderboardStatus.BLOCKED_RESEARCH)
    entry = LeaderboardEntry(entry_id="e1", leaderboard_id="lb1", candidate=c1, score=s1)
    lb = ResearchLeaderboard(leaderboard_id="lb1", cohort_id="ch1", entries=[entry])
    res = engine.select_from_leaderboard(lb)
    assert "c1" in res.rejected_candidate_ids
    assert "c1" not in res.selected_candidate_ids

def test_selection_selected_candidate():
    settings = Settings()
    settings.LEADERBOARD_SELECTION_MIN_SCORE = 70.0
    engine = CandidateSelectionEngine(settings=settings)
    c1 = ResearchCandidate(candidate_id="c1", candidate_type=CandidateType.STRATEGY, name="C1")
    s1 = CandidateScore(score_id="s1", candidate_id="c1", candidate_type=CandidateType.STRATEGY, rank_score=80.0, status=LeaderboardStatus.PASS)
    entry = LeaderboardEntry(entry_id="e1", leaderboard_id="lb1", candidate=c1, score=s1)
    lb = ResearchLeaderboard(leaderboard_id="lb1", cohort_id="ch1", entries=[entry])
    res = engine.select_from_leaderboard(lb)
    assert "c1" in res.selected_candidate_ids
