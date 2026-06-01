import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck

def test_healthcheck_financials_alanlarini_icerir(capsys):
    run_healthcheck()
    out = capsys.readouterr().out
    assert "Financials enabled" in out
