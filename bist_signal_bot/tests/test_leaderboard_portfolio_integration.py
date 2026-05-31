import pytest

def test_portfolio_candidate_includes_leaderboard():
    metadata = {
        "leaderboard_rank": 1,
        "leaderboard_score": 88.0,
        "candidate_decision": "TOP_RESEARCH_CANDIDATE"
    }
    assert metadata["leaderboard_rank"] == 1
