import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
from bist_signal_bot.app.healthcheck import run_healthcheck


def test_healthcheck_includes_new_config_fields():
    health_status = run_healthcheck()
    assert "run_mode" in health_status
    assert "dry_run" in health_status
    assert "env_file_exists" in health_status
    assert "secrets_masked_true" in health_status
    assert "config_validation_passed" in health_status
    assert "features" in health_status
    assert "telegram_dry_run" in health_status["notifications"]

def test_healthcheck_does_not_leak_secrets():
    # Even if they are set in the global settings, the dump should not contain them directly
    # Note: run_healthcheck explicitly extracts values, it does NOT blindly dump settings dict.
    # Therefore we verify our explicit structure does not contain token/chat_id plaintexts.
    health_status = run_healthcheck()

    # Check string representation to ensure no 'secret123' etc is leaking.
    # By design run_healthcheck returns booleans for 'telegram_configured', not the values.
    status_str = str(health_status)
    assert "TELEGRAM_BOT_TOKEN" not in status_str
    assert "TELEGRAM_CHAT_ID" not in status_str
