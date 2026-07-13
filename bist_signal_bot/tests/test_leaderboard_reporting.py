import pytest
from bist_signal_bot.leaderboard.reporting import format_leaderboard_report_markdown, candidate_score_to_dict
from bist_signal_bot.leaderboard.models import LeaderboardReport, CandidateScore, CandidateType, LeaderboardStatus

def test_reporting_markdown_disclaimer():
    report = LeaderboardReport(report_id="r1")
    md = format_leaderboard_report_markdown(report)
    assert "It is not investment advice or permission to trade." in md

def test_candidate_score_to_dict():
    score = CandidateScore(
        score_id="s1",
        candidate_id="c1",
        candidate_type=CandidateType.STRATEGY,
        raw_score=0.85,
        status=LeaderboardStatus.PASS
    )
    result = candidate_score_to_dict(score)
    assert result == score.model_dump()
    assert result["score_id"] == "s1"
    assert result["candidate_id"] == "c1"
    assert result["candidate_type"] == "STRATEGY"
    assert result["raw_score"] == 0.85
    assert result["status"] == "PASS"
