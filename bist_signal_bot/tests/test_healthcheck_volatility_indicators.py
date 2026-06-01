import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_volatility_indicators():
    settings = Settings()
    summary = run_healthcheck()

    assert "volatility_indicators" in summary
    vol_info = summary["volatility_indicators"]

    assert "enabled" in vol_info
    assert "feature_level" in vol_info
    assert "atr_window" in vol_info
    assert "vol_window" in vol_info
    assert "rank_window" in vol_info
    assert "annualization" in vol_info
    assert "registered_volatility_indicator_count" in vol_info
    assert "builder_instantiable" in vol_info
    assert "mock_capable" in vol_info

    assert vol_info["mock_capable"] is True
    assert vol_info["builder_instantiable"] is True
