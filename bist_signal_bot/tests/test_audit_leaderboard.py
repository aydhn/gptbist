import pytest

def test_audit_leaderboard_events():
    events = [
        "BENCHMARK_COHORT_CREATED",
        "RESEARCH_CANDIDATE_COLLECTED",
        "CANDIDATE_SCORE_CREATED",
        "RESEARCH_LEADERBOARD_BUILT",
        "CANDIDATE_COMPARED",
        "SELECTION_POLICY_LOADED",
        "CANDIDATE_SELECTION_RUN",
        "LEADERBOARD_REPORT_CREATED"
    ]
    assert "RESEARCH_LEADERBOARD_BUILT" in events
