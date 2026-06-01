import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.app.healthcheck import HealthChecker
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_performance():
    settings = Settings(ENABLE_PERFORMANCE_PROFILING=True)
    checker = HealthChecker(settings)
    res = checker.run()
    assert "performance_profiler" in res.get("components", {})
    assert res["components"]["performance_profiler"] == "OK"
