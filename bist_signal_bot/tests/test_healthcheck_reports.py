import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
from bist_signal_bot.app.healthcheck import AppHealthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_reports():
    settings = Settings(ENABLE_REPORTS=True)
    hc = AppHealthcheck(settings=settings)

    reports_status = hc._check_reports()
    assert reports_status["enabled"] is True
    assert "report_generator_instantiable" in reports_status
