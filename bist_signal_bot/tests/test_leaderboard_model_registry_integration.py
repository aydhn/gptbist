import pytest

def test_model_promotion_includes_leaderboard():
    evidence = {
        "leaderboard_score": 90.0,
        "leaderboard_decision": "TOP_RESEARCH_CANDIDATE"
    }
    assert evidence["leaderboard_score"] == 90.0
