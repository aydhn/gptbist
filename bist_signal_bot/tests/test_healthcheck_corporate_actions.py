import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck

def test_healthcheck_contains_corporate_actions():
    res = run_healthcheck()
    assert "corporate_actions" in res

    ca_info = res["corporate_actions"]
    assert "dir_path" in ca_info
    assert "file_path" in ca_info
    assert "file_exists" in ca_info
    assert "auto_initialize" in ca_info
    assert "enable_price_adjustments" in ca_info
    assert "default_policy" in ca_info
    assert "save_adjusted_data" in ca_info
    assert "apply_to_ohlc" in ca_info
    assert "apply_to_volume" in ca_info
    assert "require_verified" in ca_info
    assert "engine_instantiable" in ca_info
    assert "mock_capable" in ca_info

    assert ca_info["engine_instantiable"] is True
    assert ca_info["mock_capable"] is True
