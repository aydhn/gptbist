
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.synthetic_scenarios.storage import SyntheticScenarioStore
from bist_signal_bot.synthetic_scenarios.library import SyntheticScenarioLibrary
from bist_signal_bot.synthetic_scenarios.ohlcv import SyntheticOHLCVGenerator
from bist_signal_bot.synthetic_scenarios.macro import SyntheticMacroGenerator
from bist_signal_bot.synthetic_scenarios.breadth import SyntheticBreadthGenerator
from bist_signal_bot.synthetic_scenarios.financials import SyntheticFinancialsGenerator
from bist_signal_bot.synthetic_scenarios.events import SyntheticEventGenerator
from bist_signal_bot.synthetic_scenarios.disclosures import SyntheticDisclosureGenerator
from bist_signal_bot.synthetic_scenarios.features import SyntheticFeatureFrameGenerator
from bist_signal_bot.synthetic_scenarios.models_fixture import SyntheticModelFixtureGenerator
from bist_signal_bot.synthetic_scenarios.portfolio import SyntheticPortfolioOutcomeGenerator
from bist_signal_bot.synthetic_scenarios.stress import SyntheticStressCaseBuilder
from bist_signal_bot.synthetic_scenarios.edge_cases import SyntheticEdgeCaseFactory
from bist_signal_bot.synthetic_scenarios.generator import SyntheticScenarioGenerator
from bist_signal_bot.synthetic_scenarios.models import SyntheticScenarioGeneratorConfig
from bist_signal_bot.synthetic_scenarios.manifest import SyntheticScenarioManifestBuilder
from bist_signal_bot.synthetic_scenarios.validation import SyntheticScenarioValidator
from bist_signal_bot.storage.paths import get_synthetic_scenarios_dir

def create_synthetic_scenario_store(settings: Settings | None = None, base_dir: Path | None = None) -> SyntheticScenarioStore:
    path = base_dir or get_synthetic_scenarios_dir(settings)
    return SyntheticScenarioStore(path)

def create_synthetic_scenario_library(settings: Settings | None = None, base_dir: Path | None = None) -> SyntheticScenarioLibrary:
    return SyntheticScenarioLibrary()

def create_synthetic_ohlcv_generator(settings: Settings | None = None) -> SyntheticOHLCVGenerator:
    return SyntheticOHLCVGenerator()

def create_synthetic_macro_generator(settings: Settings | None = None) -> SyntheticMacroGenerator:
    return SyntheticMacroGenerator()

def create_synthetic_breadth_generator(settings: Settings | None = None) -> SyntheticBreadthGenerator:
    return SyntheticBreadthGenerator()

def create_synthetic_financials_generator(settings: Settings | None = None) -> SyntheticFinancialsGenerator:
    return SyntheticFinancialsGenerator()

def create_synthetic_event_generator(settings: Settings | None = None) -> SyntheticEventGenerator:
    return SyntheticEventGenerator()

def create_synthetic_disclosure_generator(settings: Settings | None = None) -> SyntheticDisclosureGenerator:
    return SyntheticDisclosureGenerator()

def create_synthetic_feature_frame_generator(settings: Settings | None = None) -> SyntheticFeatureFrameGenerator:
    return SyntheticFeatureFrameGenerator()

def create_synthetic_model_fixture_generator(settings: Settings | None = None) -> SyntheticModelFixtureGenerator:
    return SyntheticModelFixtureGenerator()

def create_synthetic_portfolio_outcome_generator(settings: Settings | None = None) -> SyntheticPortfolioOutcomeGenerator:
    return SyntheticPortfolioOutcomeGenerator()

def create_synthetic_stress_case_builder(settings: Settings | None = None) -> SyntheticStressCaseBuilder:
    return SyntheticStressCaseBuilder()

def create_synthetic_edge_case_factory(settings: Settings | None = None) -> SyntheticEdgeCaseFactory:
    return SyntheticEdgeCaseFactory()

def create_synthetic_scenario_generator(settings: Settings | None = None, base_dir: Path | None = None) -> SyntheticScenarioGenerator:
    config = SyntheticScenarioGeneratorConfig(
        ohlcv_gen=create_synthetic_ohlcv_generator(settings),
        macro_gen=create_synthetic_macro_generator(settings),
        breadth_gen=create_synthetic_breadth_generator(settings),
        fin_gen=create_synthetic_financials_generator(settings),
        evt_gen=create_synthetic_event_generator(settings),
        disc_gen=create_synthetic_disclosure_generator(settings),
        feature_gen=create_synthetic_feature_frame_generator(settings),
        model_fix_gen=create_synthetic_model_fixture_generator(settings),
        port_gen=create_synthetic_portfolio_outcome_generator(settings),
        stress_bld=create_synthetic_stress_case_builder(settings),
        edge_fac=create_synthetic_edge_case_factory(settings)
    )
    return SyntheticScenarioGenerator(config)

def create_synthetic_scenario_manifest_builder(settings: Settings | None = None, base_dir: Path | None = None) -> SyntheticScenarioManifestBuilder:
    return SyntheticScenarioManifestBuilder()

def create_synthetic_scenario_validator(settings: Settings | None = None, base_dir: Path | None = None) -> SyntheticScenarioValidator:
    return SyntheticScenarioValidator()
