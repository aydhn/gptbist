import pytest
from bist_signal_bot.security.config_audit import ConfigSecurityAuditor
from bist_signal_bot.security.kill_switch import KillSwitchManager
from bist_signal_bot.config.settings import Settings

def test_config_audit_produces_report(tmp_path):
    settings = Settings()
    ks_manager = KillSwitchManager(settings, tmp_path)
    auditor = ConfigSecurityAuditor(ks_manager)

    report = auditor.audit_settings(settings)
    assert report is not None
    assert len(report.checks) > 0

def test_config_audit_paper_default_active_warning(tmp_path):
    settings = Settings(RUNTIME_USE_PAPER=True, SECURITY_WARN_IF_PAPER_DEFAULT_ACTIVE=True)
    ks_manager = KillSwitchManager(settings, tmp_path)
    auditor = ConfigSecurityAuditor(ks_manager)

    report = auditor.audit_settings(settings)
    assert any("RUNTIME_USE_PAPER is active by default" in w for w in report.warnings)
