import pandas as pd
from typing import Dict, Any
import uuid

from bist_signal_bot.validation.models import CostRobustnessResult, StrategyValidationRequest, ValidationStatus

class CostRobustnessAnalyzer:
    def analyze(self, strategy_name: str, symbol: str, data: pd.DataFrame, base_parameters: Dict[str, Any], request: StrategyValidationRequest) -> CostRobustnessResult:
        if data.empty:
            return CostRobustnessResult(
                cost_result_id=f"COST_{uuid.uuid4().hex[:8]}",
                strategy_name=strategy_name,
                symbol=symbol,
                status=ValidationStatus.INSUFFICIENT_DATA,
                warnings=["Insufficient data"]
            )
        return CostRobustnessResult(
            cost_result_id=f"COST_{uuid.uuid4().hex[:8]}",
            strategy_name=strategy_name,
            symbol=symbol,
            status=ValidationStatus.PASS
        )

    def calculate_cost_sensitivity(self, scenario_metrics: Dict[str, Dict[str, Any]]) -> float | None:
        base = scenario_metrics.get("BASE", {}).get("net_return_pct")
        stress = scenario_metrics.get("STRESS", {}).get("net_return_pct")
        if base is None or stress is None or base <= 0: return None
        return ((base - stress) / base) * 100
