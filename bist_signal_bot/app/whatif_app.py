import logging
from pathlib import Path
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.whatif.scenarios import WhatIfScenarioFactory
from bist_signal_bot.whatif.assumptions import AssumptionOverrideEngine
from bist_signal_bot.whatif.sensitivity import SensitivityAnalyzer
from bist_signal_bot.whatif.capital_scaling import CapitalScalingAnalyzer
from bist_signal_bot.whatif.policy_sandbox import PolicySandbox
from bist_signal_bot.whatif.counterfactual import CounterfactualEngine
from bist_signal_bot.whatif.comparison import WhatIfComparisonEngine
from bist_signal_bot.whatif.engine import WhatIfEngine
from bist_signal_bot.whatif.storage import WhatIfStore

logger = logging.getLogger(__name__)

def create_whatif_scenario_factory(settings: Settings | None = None) -> WhatIfScenarioFactory:
    settings = settings or get_settings()
    return WhatIfScenarioFactory()

def create_assumption_override_engine(settings: Settings | None = None) -> AssumptionOverrideEngine:
    settings = settings or get_settings()
    return AssumptionOverrideEngine(logger=logger)

def create_sensitivity_analyzer(settings: Settings | None = None) -> SensitivityAnalyzer:
    settings = settings or get_settings()
    return SensitivityAnalyzer(settings=settings, logger=logger)

def create_capital_scaling_analyzer(settings: Settings | None = None, base_dir: Path | None = None) -> CapitalScalingAnalyzer:
    settings = settings or get_settings()
    counterfactual = create_counterfactual_engine(settings=settings, base_dir=base_dir)
    return CapitalScalingAnalyzer(settings=settings, counterfactual_engine=counterfactual, logger=logger)

def create_policy_sandbox(settings: Settings | None = None, base_dir: Path | None = None) -> PolicySandbox:
    settings = settings or get_settings()
    counterfactual = create_counterfactual_engine(settings=settings, base_dir=base_dir)
    return PolicySandbox(settings=settings, counterfactual_engine=counterfactual, logger=logger)

def create_counterfactual_engine(settings: Settings | None = None, base_dir: Path | None = None) -> CounterfactualEngine:
    settings = settings or get_settings()
    assump = create_assumption_override_engine(settings=settings)
    return CounterfactualEngine(settings=settings, assumption_engine=assump, logger=logger)

def create_whatif_comparison_engine(settings: Settings | None = None) -> WhatIfComparisonEngine:
    settings = settings or get_settings()
    return WhatIfComparisonEngine(settings=settings, logger=logger)

def create_whatif_store(settings: Settings | None = None, base_dir: Path | None = None) -> WhatIfStore:
    settings = settings or get_settings()
    return WhatIfStore(settings=settings, base_dir=base_dir)

def create_whatif_engine(settings: Settings | None = None, base_dir: Path | None = None) -> WhatIfEngine:
    settings = settings or get_settings()
    return WhatIfEngine(
        scenario_factory=create_whatif_scenario_factory(settings),
        assumption_engine=create_assumption_override_engine(settings),
        counterfactual_engine=create_counterfactual_engine(settings, base_dir),
        comparison_engine=create_whatif_comparison_engine(settings),
        sensitivity_analyzer=create_sensitivity_analyzer(settings),
        capital_scaling_analyzer=create_capital_scaling_analyzer(settings, base_dir),
        policy_sandbox=create_policy_sandbox(settings, base_dir),
        store=create_whatif_store(settings, base_dir),
        settings=settings,
        logger=logger
    )
