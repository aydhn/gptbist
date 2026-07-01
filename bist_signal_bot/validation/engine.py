import pandas as pd
from typing import List, Dict, Any
import uuid
from datetime import datetime
import logging

from bist_signal_bot.validation.models import StrategyValidationRequest, StrategyValidationResult, ValidationSplitType
from bist_signal_bot.validation.splits import ValidationSplitBuilder
from bist_signal_bot.validation.walk_forward import WalkForwardValidator
from bist_signal_bot.validation.purged_cv import PurgedCVValidator
from bist_signal_bot.validation.parameter_stability import ParameterStabilityAnalyzer
from bist_signal_bot.validation.overfit import OverfitDiagnosticsEngine
from bist_signal_bot.validation.regime_robustness import RegimeRobustnessAnalyzer
from bist_signal_bot.validation.cost_robustness import CostRobustnessAnalyzer
from bist_signal_bot.validation.scoring import StrategyValidationScorer
from bist_signal_bot.validation.storage import ValidationStore
from bist_signal_bot.config.settings import Settings

from dataclasses import dataclass

@dataclass
class ValidationEngineDependencies:
    split_builder: ValidationSplitBuilder
    walk_forward_validator: WalkForwardValidator
    purged_cv_validator: PurgedCVValidator
    parameter_stability_analyzer: ParameterStabilityAnalyzer
    overfit_diagnostics: OverfitDiagnosticsEngine
    regime_robustness: RegimeRobustnessAnalyzer
    cost_robustness: CostRobustnessAnalyzer
    scorer: StrategyValidationScorer
    store: ValidationStore
    settings: Settings

# ContextFusion collects validation overfit warnings
class StrategyValidationEngine:
    def __init__(self, deps: ValidationEngineDependencies):
        self.split_builder = deps.split_builder
        self.walk_forward_validator = deps.walk_forward_validator
        self.purged_cv_validator = deps.purged_cv_validator
        self.parameter_stability_analyzer = deps.parameter_stability_analyzer
        self.overfit_diagnostics = deps.overfit_diagnostics
        self.regime_robustness = deps.regime_robustness
        self.cost_robustness = deps.cost_robustness
        self.scorer = deps.scorer
        self.store = deps.store
        self.settings = deps.settings

    def validate_strategy(self, request: StrategyValidationRequest) -> StrategyValidationResult:
        data = pd.DataFrame()
        wfs = []
        cvs = []
        for sym in request.symbols:
            if request.split_type == ValidationSplitType.WALK_FORWARD:
                splits = self.split_builder.build_rolling_splits(
                    datetime(2020, 1, 1), datetime(2023, 1, 1),
                    request.train_window_days, request.test_window_days, request.step_days
                )
            else:
                splits = []
            wf = self.walk_forward_validator.run(request.strategy_name, sym, data, request, splits)
            wfs.append(wf)

            cv_splits = self.split_builder.build_purged_kfold_splits(
                [datetime(2020, 1, 1), datetime(2023, 1, 1)], request.folds, request.purge_days, request.embargo_days
            )
            cv = self.purged_cv_validator.run(request.strategy_name, sym, data, request, cv_splits)
            cvs.append(cv)

        return StrategyValidationResult(
            validation_id=f"VAL_{uuid.uuid4().hex[:8]}",
            request=request,
            walk_forward_results=wfs,
            purged_cv_results=cvs
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> 'StrategyValidationEngine':
        from bist_signal_bot.storage.paths import get_validation_dir
        store = ValidationStore(get_validation_dir(settings))
        deps = ValidationEngineDependencies(
            split_builder=ValidationSplitBuilder(),
            walk_forward_validator=WalkForwardValidator(),
            purged_cv_validator=PurgedCVValidator(),
            parameter_stability_analyzer=ParameterStabilityAnalyzer(),
            overfit_diagnostics=OverfitDiagnosticsEngine(),
            regime_robustness=RegimeRobustnessAnalyzer(),
            cost_robustness=CostRobustnessAnalyzer(),
            scorer=StrategyValidationScorer(),
            store=store,
            settings=settings
        )
        return cls(deps)
