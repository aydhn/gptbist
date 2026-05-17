import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.release.compatibility import CompatibilityChecker
from bist_signal_bot.release.models import ReleaseCheckStatus

def test_compatibility_checker_python():
    c = CompatibilityChecker(Settings())
    res = c.check_python_compatibility()
    assert res.status == ReleaseCheckStatus.PASS # We assume this runs on >= 3.10

def test_compatibility_checker_optional_deps():
    c = CompatibilityChecker(Settings())
    res = c.check_dependency_compatibility()
    opt = [x for x in res if x.check_id == "compat_opt_deps"][0]
    assert opt.status == ReleaseCheckStatus.WARN
