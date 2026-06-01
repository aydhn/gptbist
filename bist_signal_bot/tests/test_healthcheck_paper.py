import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_paper():
    # 46. Healthcheck paper trading alanlarını içerir.
    settings = Settings()
    # Mock some dependencies if needed or just let it run
    res = run_healthcheck(settings)
    assert "paper_trading" in res
    assert res["paper_trading"]["status"] in ["healthy", "unhealthy"]
    assert "execution_mode" in res["paper_trading"]
