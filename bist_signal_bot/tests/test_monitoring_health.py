from bist_signal_bot.monitoring.health import MonitoringHealthEngine

def test_health_score():
    eng = MonitoringHealthEngine()
    score = eng.health_score([], [])
    assert score is None

    score2 = eng.health_score(["dummy_metric"], [])
    assert score2 == 100.0

    score3 = eng.health_score(["dummy_metric"], ["dummy_decay"])
    assert score3 == 90.0
