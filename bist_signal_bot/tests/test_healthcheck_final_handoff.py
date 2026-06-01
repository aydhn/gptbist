import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import sys
from unittest.mock import MagicMock
sys.modules['bist_signal_bot.config.settings'] = MagicMock()
import pytest

def test_healthcheck_final_handoff_status():
    from bist_signal_bot.app.healthcheck import check_final_handoff
    res = check_final_handoff()
    assert "final_handoff_enabled" in res
    assert "latest_handoff_status" in res

def test_doctor_final_handoff_missing_playbook():
    from bist_signal_bot.maintenance.doctor import check_final_handoff_health
    issues = check_final_handoff_health()
    assert any("Missing operator playbook" in i for i in issues)

def test_release_gate_include_final_handoff():
    from bist_signal_bot.qa.release_gate import check_final_handoff_gate
    status, msg = check_final_handoff_gate()
    assert status in ("FAIL", "WATCH")
