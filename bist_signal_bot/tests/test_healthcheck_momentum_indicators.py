import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck

def test_healthcheck_includes_momentum_indicators():
    hc = run_healthcheck()
    assert "momentum_indicators" in hc

    mom_hc = hc["momentum_indicators"]
    assert "enabled" in mom_hc
    assert "feature_level" in mom_hc
    assert "rsi_window" in mom_hc
    assert "cci_window" in mom_hc
    assert mom_hc["registered_momentum_indicator_count"] > 0
    assert mom_hc["builder_instantiable"] is True
    assert mom_hc["mock_capable"] is True
