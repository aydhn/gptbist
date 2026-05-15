import pytest

from bist_signal_bot.quality.test_runner import QualityTestRunner
from bist_signal_bot.quality.coverage import CoverageRunner
from bist_signal_bot.quality.static_analysis import StaticAnalysisRunner
from bist_signal_bot.quality.type_checking import TypeCheckRunner
from bist_signal_bot.quality.import_checks import ImportCheckRunner
from bist_signal_bot.quality.security_checks import QualitySecurityRunner
from bist_signal_bot.quality.regression import RegressionSmokeRunner
from bist_signal_bot.quality.gate import QualityGateRunner
from bist_signal_bot.quality.models import QualitySuite, QualityGateLevel, QualityRunConfig
from bist_signal_bot.quality.storage import QualityReportStore

def test_imports_all():
    assert QualityTestRunner is not None
    assert CoverageRunner is not None
    assert StaticAnalysisRunner is not None
    assert TypeCheckRunner is not None
    assert ImportCheckRunner is not None
    assert QualitySecurityRunner is not None
    assert RegressionSmokeRunner is not None
    assert QualityGateRunner is not None
    assert QualityReportStore is not None
    print("All modules imported successfully.")
