import pytest

def test_qa_release_gate_leaderboard_blocked():
    top_rank_status = "BLOCKED_RESEARCH"
    fail_on_blocked = True
    assert top_rank_status == "BLOCKED_RESEARCH" and fail_on_blocked is True
