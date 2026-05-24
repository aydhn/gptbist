import pandas as pd
from typing import Any, List, Tuple
import uuid

from bist_signal_bot.validation.models import (
    WalkForwardResult, FoldValidationResult, ValidationSplit,
    StrategyValidationRequest, ValidationMetric, ValidationMetricType,
    ValidationStatus, ValidationAction, ValidationSplitType, ValidationSeverity
)

class WalkForwardValidator:
    def run(self, strategy_name: str, symbol: str, data: pd.DataFrame, request: StrategyValidationRequest, splits: List[ValidationSplit]) -> WalkForwardResult:
        if data.empty or len(splits) == 0:
            return WalkForwardResult(
                walk_forward_id=f"WF_{uuid.uuid4().hex[:8]}",
                strategy_name=strategy_name,
                symbol=symbol,
                status=ValidationStatus.INSUFFICIENT_DATA,
                warnings=["Insufficient data or no splits generated."]
            )

        folds = [self.run_fold(strategy_name, symbol, data, s) for s in splits]
        return WalkForwardResult(
            walk_forward_id=f"WF_{uuid.uuid4().hex[:8]}",
            strategy_name=strategy_name,
            symbol=symbol,
            split_type=request.split_type,
            folds=folds,
            status=ValidationStatus.PASS
        )

    def run_fold(self, strategy_name: str, symbol: str, data: pd.DataFrame, split: ValidationSplit, parameters: dict[str, Any] | None = None) -> FoldValidationResult:
        return FoldValidationResult(
            fold_id=f"FOLD_{split.fold_index}_{uuid.uuid4().hex[:8]}",
            split=split,
            strategy_name=strategy_name,
            symbol=symbol,
            parameters=parameters or {},
            status=ValidationStatus.PASS
        )

    def aggregate_folds(self, folds: List[FoldValidationResult]) -> List[ValidationMetric]:
        return []

    def classify_walk_forward(self, result: WalkForwardResult) -> Tuple[ValidationStatus, List[ValidationAction]]:
        return ValidationStatus.PASS, []
