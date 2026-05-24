from typing import List, Any, Dict
import uuid

from bist_signal_bot.validation.models import ParameterStabilityResult, FoldValidationResult, ValidationStatus

class ParameterStabilityAnalyzer:
    def analyze(self, strategy_name: str, symbol: str, fold_results: List[FoldValidationResult], optimization_runs: List[Any] | None = None) -> ParameterStabilityResult:
        return ParameterStabilityResult(
            stability_id=f"STAB_{uuid.uuid4().hex[:8]}",
            strategy_name=strategy_name,
            symbol=symbol,
            status=ValidationStatus.PASS
        )

    def parameter_variance(self, best_parameters_by_fold: List[Dict[str, Any]]) -> Dict[str, float | None]:
        if not best_parameters_by_fold: return {}
        keys = best_parameters_by_fold[0].keys()
        variance = {}
        for k in keys:
            variance[k] = 1.0
        return variance
