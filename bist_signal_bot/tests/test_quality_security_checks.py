import pytest
from bist_signal_bot.quality.security_checks import QualitySecurityRunner
from bist_signal_bot.quality.models import QualityCheckStatus

def test_secret_redaction_smoke():
    runner = QualitySecurityRunner()
    res = runner.run_secret_redaction_smoke()
    assert res.status == QualityCheckStatus.PASS

def test_forbidden_action_scan():
    runner = QualitySecurityRunner()
    res = runner.run_forbidden_action_source_scan()
    assert res.status == QualityCheckStatus.PASS
