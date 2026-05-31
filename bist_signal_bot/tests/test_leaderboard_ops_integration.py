import pytest

def test_ops_staleness_leaderboard():
    report_age_hours = 25
    stale_threshold = 24
    assert report_age_hours > stale_threshold
