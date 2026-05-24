import pytest
import pandas as pd
from pathlib import Path
from bist_signal_bot.validation.engine import StrategyValidationEngine
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.validation.models import StrategyValidationRequest
from bist_signal_bot.validation.splits import ValidationSplitBuilder
from bist_signal_bot.validation.walk_forward import WalkForwardValidator
from bist_signal_bot.validation.purged_cv import PurgedCVValidator
from bist_signal_bot.validation.parameter_stability import ParameterStabilityAnalyzer
from bist_signal_bot.validation.overfit import OverfitDiagnosticsEngine
from bist_signal_bot.validation.regime_robustness import RegimeRobustnessAnalyzer
from bist_signal_bot.validation.cost_robustness import CostRobustnessAnalyzer
from bist_signal_bot.validation.scoring import StrategyValidationScorer
from bist_signal_bot.validation.storage import ValidationStore

def test_strategy_validation_engine_single_symbol(tmp_path):
    store = ValidationStore(tmp_path)
    engine = StrategyValidationEngine(
        split_builder=ValidationSplitBuilder(),
        walk_forward_validator=WalkForwardValidator(),
        purged_cv_validator=PurgedCVValidator(),
        parameter_stability_analyzer=ParameterStabilityAnalyzer(),
        overfit_diagnostics=OverfitDiagnosticsEngine(),
        regime_robustness=RegimeRobustnessAnalyzer(),
        cost_robustness=CostRobustnessAnalyzer(),
        scorer=StrategyValidationScorer(),
        store=store,
        settings=Settings()
    )

    req = StrategyValidationRequest(
        strategy_name="MA",
        symbols=["ASELS"],
        save_output=True
    )

    res = engine.validate_strategy(req)
    assert len(res.walk_forward_results) == 1
    assert len(res.purged_cv_results) == 1
