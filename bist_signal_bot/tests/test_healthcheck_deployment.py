from bist_signal_bot.app.healthcheck import HealthChecker
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_deployment():
    settings = Settings()
    checker = HealthChecker(settings)
    res = checker.run()
    assert "deployment" in res["components"]
    assert "enabled" in res["components"]["deployment"]
