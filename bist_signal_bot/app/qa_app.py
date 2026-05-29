from bist_signal_bot.qa.storage import QAStore
from bist_signal_bot.qa.fixtures import QAFixtureManager
from bist_signal_bot.qa.synthetic_data import SyntheticDataBuilder
from bist_signal_bot.qa.scenarios import QAScenarioFactory
from bist_signal_bot.qa.replay import ScenarioReplayEngine
from bist_signal_bot.qa.smoke import SmokeTestRunner
from bist_signal_bot.qa.regression import RegressionMatrixBuilder
from bist_signal_bot.qa.release_gate import ReleaseGateRunner
from bist_signal_bot.qa.reproducibility import ReproducibilityPackBuilder
from bist_signal_bot.qa.safety_checks import QASafetyChecker
from bist_signal_bot.qa.no_external_calls import NoExternalCallGuard
from bist_signal_bot.qa.coverage_matrix import QACoverageMatrix
from bist_signal_bot.qa.cli_smoke_matrix import CLISmokeMatrix
from pathlib import Path

def create_qa_store(settings=None, base_dir=None) -> QAStore:
    return QAStore(settings, base_dir)

def create_qa_fixture_manager(settings=None, base_dir=None) -> QAFixtureManager:
    return QAFixtureManager(settings, base_dir)

def create_synthetic_data_builder(settings=None) -> SyntheticDataBuilder:
    return SyntheticDataBuilder(settings)

def create_qa_scenario_factory(settings=None) -> QAScenarioFactory:
    return QAScenarioFactory(settings)

def create_scenario_replay_engine(settings=None, base_dir=None) -> ScenarioReplayEngine:
    return ScenarioReplayEngine(settings, base_dir)

def create_smoke_test_runner(settings=None, base_dir=None) -> SmokeTestRunner:
    return SmokeTestRunner(settings, base_dir)

def create_regression_matrix_builder(settings=None) -> RegressionMatrixBuilder:
    return RegressionMatrixBuilder(settings)

def create_release_gate_runner(settings=None, base_dir=None) -> ReleaseGateRunner:
    return ReleaseGateRunner(settings, base_dir)

def create_reproducibility_pack_builder(settings=None, base_dir=None) -> ReproducibilityPackBuilder:
    return ReproducibilityPackBuilder(settings, base_dir)

def create_qa_safety_checker(settings=None, base_dir=None) -> QASafetyChecker:
    return QASafetyChecker(settings, base_dir)

def create_no_external_call_guard(settings=None) -> NoExternalCallGuard:
    return NoExternalCallGuard(settings)

def create_qa_coverage_matrix(settings=None) -> QACoverageMatrix:
    return QACoverageMatrix(settings)

def create_cli_smoke_matrix(settings=None) -> CLISmokeMatrix:
    return CLISmokeMatrix(settings)
