from bist_signal_bot.app.healthcheck import get_health_status

class DummyArgs:
    monitoring = True

def test_healthcheck_monitoring():
    res = get_health_status(DummyArgs())
    assert res['monitoring_enabled'] is True
