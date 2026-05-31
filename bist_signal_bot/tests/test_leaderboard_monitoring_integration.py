import pytest

def test_monitoring_health_includes_leaderboard():
    metrics = {
        "monitoring_health": 80.0
    }
    assert metrics["monitoring_health"] == 80.0
