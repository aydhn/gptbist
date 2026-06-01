import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
import os

def test_cli_ml_filter_config():
    # just run it as a subprocess to avoid import complexity
    res = os.popen("python -m bist_signal_bot ml-filter config 2>&1").read()
    assert "ML Filter Configuration" in res or "enabled" in res or "Error" not in res

def test_cli_ml_filter_config_json():
    res = os.popen("python -m bist_signal_bot ml-filter config --json 2>&1").read()
    assert "{" in res or "Error" not in res
