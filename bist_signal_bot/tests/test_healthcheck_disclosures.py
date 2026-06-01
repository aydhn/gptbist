import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
import io
import contextlib
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings
def test_healthcheck_disclosures():
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        run_healthcheck(settings=Settings(), as_json=False)
    out = f.getvalue()
    assert "Healthcheck Pass" in out
    assert "Disclosure Intelligence Enabled: True" in out
