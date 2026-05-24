from typing import List, Any, Dict, Tuple
import uuid
import pandas as pd

from bist_signal_bot.validation.models import (
    OverfitDiagnosticsResult, WalkForwardResult, PurgedCVResult,
    ParameterStabilityResult, FoldValidationResult, ValidationStatus,
    ValidationSeverity, ValidationAction
)

class OverfitDiagnosticsEngine:
    def diagnose(self, strategy_name: str, symbol: str, walk_forward: WalkForwardResult | None = None, purged_cv: PurgedCVResult | None = None, stability: ParameterStabilityResult | None = None, optimization_runs: List[Any] | None = None) -> OverfitDiagnosticsResult:
        return OverfitDiagnosticsResult(
            diagnostics_id=f"OVD_{uuid.uuid4().hex[:8]}",
            strategy_name=strategy_name,
            symbol=symbol,
            status=ValidationStatus.PASS
        )

    def calculate_oos_decay(self, in_sample: Dict[str, Any], out_of_sample: Dict[str, Any]) -> float | None:
        is_ret = in_sample.get("median_return")
        oos_ret = out_of_sample.get("median_return")
        if is_ret is None or oos_ret is None or is_ret <= 0: return None
        decay = ((is_ret - oos_ret) / is_ret) * 100
        return max(0.0, decay)

    def calculate_overfit_score(self, oos_decay_pct: float | None, parameter_instability: float | None, concentration: float | None) -> float | None:
        components = [c for c in [oos_decay_pct, parameter_instability, concentration] if c is not None]
        if not components: return None
        return sum(components) / len(components)

    def classify_overfit(self, score: float | None) -> Tuple[ValidationStatus, ValidationSeverity, List[ValidationAction]]:
        if score is None: return ValidationStatus.UNKNOWN, ValidationSeverity.INFO, []
        if score > 70.0: return ValidationStatus.FAIL, ValidationSeverity.CRITICAL, [ValidationAction.AVOID_AUTO_SELECTION]
        if score > 40.0: return ValidationStatus.WATCH, ValidationSeverity.HIGH, [ValidationAction.WATCH]
        return ValidationStatus.PASS, ValidationSeverity.INFO, []
