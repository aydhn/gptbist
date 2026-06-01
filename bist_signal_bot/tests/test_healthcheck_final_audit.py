import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_final_audit(tmp_path):
    settings = Settings()
    settings.ENABLE_FINAL_AUDIT = True
    settings.DATA_DIR = str(tmp_path)

    res = run_healthcheck(settings=settings, as_json=False)

    assert "final_audit" in res
    assert res["final_audit"]["enabled"] is True
    assert "acceptance_status" in res["final_audit"]
    assert "security_audit_status" in res["final_audit"]
