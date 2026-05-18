import pytest
from bist_signal_bot.app.healthcheck import AppHealthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_data_v2():
    settings = Settings(ENABLE_DATA_PROVIDER_V2=True)
    hc = AppHealthcheck(settings)

    status = hc.run()
    assert "data_provider_v2" in status
    assert status["data_provider_v2"]["enabled"] is True
    assert status["data_provider_v2"]["allow_network"] is False
    assert status["data_provider_v2"]["local_file_enabled"] is True
