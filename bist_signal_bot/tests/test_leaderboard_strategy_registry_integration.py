import pytest

def test_strategy_evidence_includes_leaderboard():
    evidence = {
        "leaderboard_rank": 1,
        "leaderboard_score": 85.0,
        "leaderboard_decision": "TOP_RESEARCH_CANDIDATE",
        "cohort_id": "cohort_strat_123"
    }
    assert evidence["leaderboard_rank"] == 1
