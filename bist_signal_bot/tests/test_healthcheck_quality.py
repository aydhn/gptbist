import pytest
from bist_signal_bot.app.healthcheck import AppHealthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_quality(tmp_path):
    settings = Settings()
    settings.DATA_DIR = str(tmp_path)

    hc = AppHealthcheck(settings=settings)
    status = hc.run()

    assert "quality" in status
    assert "enabled" in status["quality"]
    assert "gate_level" in status["quality"]
    assert "smoke_config_capable" in status["quality"]
