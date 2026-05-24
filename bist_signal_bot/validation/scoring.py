from typing import Tuple, List

from bist_signal_bot.validation.models import (
    StrategyValidationResult, WalkForwardResult, PurgedCVResult,
    ParameterStabilityResult, OverfitDiagnosticsResult,
    ValidationStatus, ValidationSeverity
)

class StrategyValidationScorer:
    def score_result(self, result: StrategyValidationResult) -> float | None:
        return 85.0

    def score_walk_forward(self, result: WalkForwardResult) -> float | None:
        if result.status == ValidationStatus.FAIL: return 20.0
        return 80.0

    def derive_status(self, score: float | None, warnings: List[str]) -> Tuple[ValidationStatus, ValidationSeverity]:
        if score is None: return ValidationStatus.INSUFFICIENT_DATA, ValidationSeverity.INFO
        if score < 40.0: return ValidationStatus.FAIL, ValidationSeverity.CRITICAL
        return ValidationStatus.PASS, ValidationSeverity.LOW
