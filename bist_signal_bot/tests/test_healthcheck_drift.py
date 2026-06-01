import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_drift():
    s = Settings()
    s.ENABLE_DRIFT_MONITORING = True
    res = run_healthcheck(s)
    assert res["status"] == "OK"
    assert res["components"]["drift_monitoring"] == "OK"

    s.ENABLE_DRIFT_MONITORING = False
    res2 = run_healthcheck(s)
    assert res2["components"]["drift_monitoring"] == "DISABLED"
