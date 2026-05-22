import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_telegram(monkeypatch):
    settings = Settings(ENABLE_TELEGRAM_CENTER=True)
    # mock to avoid knowledge base error
    monkeypatch.setattr('bist_signal_bot.app.healthcheck.HealthChecker.run', lambda self: {"status": "OK"})

    # We added it directly to run_healthcheck wrapper
    res = run_healthcheck(settings)
    assert 'telegram_center' in res
