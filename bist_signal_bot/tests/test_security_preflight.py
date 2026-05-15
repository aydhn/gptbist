import pytest
from bist_signal_bot.security.preflight import SecurityPreflightRunner
from bist_signal_bot.security.kill_switch import KillSwitchManager
from bist_signal_bot.security.models import KillSwitchScope
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import SecurityPreflightError, SecretLeakError

def test_preflight_fails_when_runtime_kill_switch_active(tmp_path):
    settings = Settings()
    ks_manager = KillSwitchManager(settings, tmp_path)
    ks_manager.activate([KillSwitchScope.RUNTIME], "test")

    runner = SecurityPreflightRunner(settings, kill_switch=ks_manager)
    with pytest.raises(SecurityPreflightError):
        runner.run_runtime_preflight()

def test_preflight_blocks_notification_with_secret(tmp_path):
    settings = Settings(SECURITY_FAIL_ON_SECRET_LEAK=True)
    runner = SecurityPreflightRunner(settings)

    payload = {"bot_token": "123456789:ABCDefghIJKLmnopQRSTuvwxyz123456789"}
    with pytest.raises(SecretLeakError):
        runner.run_notification_preflight(payload)

def test_preflight_report_sanitizes_unsafe_claims(tmp_path):
    settings = Settings(SECURITY_BLOCK_UNSAFE_CLAIMS=True)
    runner = SecurityPreflightRunner(settings)

    payload = {"msg": "kesin al"}
    # Because claim_guard validation throws an error if it finds unsafe claims,
    # the preflight will raise if the payload hasn't been sanitized prior.
    from bist_signal_bot.core.exceptions import UnsafeClaimError
    with pytest.raises(UnsafeClaimError):
        runner.run_report_preflight(payload)
