import pandas as pd
from typing import List, Any
import uuid

from bist_signal_bot.validation.models import (
    PurgedCVResult, FoldValidationResult, ValidationSplit,
    StrategyValidationRequest, ValidationMetric, ValidationStatus
)

class PurgedCVValidator:
    def run(self, strategy_name: str, symbol: str, data: pd.DataFrame, request: StrategyValidationRequest, splits: List[ValidationSplit]) -> PurgedCVResult:
        if data.empty or not splits:
            return PurgedCVResult(
                cv_id=f"CV_{uuid.uuid4().hex[:8]}",
                strategy_name=strategy_name,
                symbol=symbol,
                status=ValidationStatus.INSUFFICIENT_DATA,
                leakage_warnings=["Insufficient data"]
            )
        leakage_warnings = self.detect_leakage_risk(splits)
        return PurgedCVResult(
            cv_id=f"CV_{uuid.uuid4().hex[:8]}",
            strategy_name=strategy_name,
            symbol=symbol,
            folds=[],
            purge_days=request.purge_days,
            embargo_days=request.embargo_days,
            leakage_warnings=leakage_warnings,
            status=ValidationStatus.PASS if not leakage_warnings else ValidationStatus.WATCH
        )

    def detect_leakage_risk(self, splits: List[ValidationSplit]) -> List[str]:
        warnings = []
        for split in splits:
            if split.purge_days == 0 and split.embargo_days == 0:
                warnings.append("High leakage risk")
        return warnings
