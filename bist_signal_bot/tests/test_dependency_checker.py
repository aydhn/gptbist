import pytest
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.packaging.dependencies import DependencyChecker
from bist_signal_bot.packaging.models import DependencyStatus

def test_parse_requirements_file(tmp_path):
    req_file = tmp_path / "reqs.txt"
    req_file.write_text("pandas>=2.0.0\nnumpy # A comment\n\nrequests", encoding="utf-8")

    checker = DependencyChecker(Settings())
    reqs = checker.parse_requirements_file(req_file)
    assert reqs == ["pandas>=2.0.0", "numpy", "requests"]

def test_check_package_installed():
    checker = DependencyChecker(Settings())
    # pytest should be installed since we are running tests
    res = checker.check_package("pytest>=7.0.0")
    assert res.package_name == "pytest"
    assert res.status == DependencyStatus.INSTALLED

def test_check_package_missing():
    checker = DependencyChecker(Settings())
    res = checker.check_package("some_nonexistent_pkg_123")
    assert res.package_name == "some_nonexistent_pkg_123"
    assert res.status == DependencyStatus.MISSING

def test_check_package_optional_missing():
    checker = DependencyChecker(Settings())
    res = checker.check_package("some_nonexistent_pkg_123", optional=True)
    assert res.status == DependencyStatus.OPTIONAL_MISSING
