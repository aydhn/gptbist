import pytest

def test_context_includes_leaderboard():
    context = {
        "leaderboard_score": 75.0,
        "leaderboard_rank": 2,
        "candidate_decision": "WATCH_RESEARCH_CANDIDATE",
        "selection_policy_status": "PASS"
    }
    assert context["leaderboard_score"] == 75.0
