import uuid
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.whatif.models import (
    WhatIfRunRequest, CapitalScalingResult, WhatIfScenarioResult, WhatIfScenario,
    WhatIfScenarioType, AssumptionType, WhatIfAssumptionOverride
)

class CapitalScalingAnalyzer:
    def __init__(self, settings: Settings, counterfactual_engine: Any, logger: Any):
        self.settings = settings
        self.counterfactual_engine = counterfactual_engine
        self.logger = logger

    def run_scaling(self, base_request: WhatIfRunRequest, notionals: list[float]) -> CapitalScalingResult:
        scenarios = self.build_notional_scenarios(notionals)
        scenario_results = []

        for sc in scenarios:
            result = self.counterfactual_engine.run_counterfactual(base_request, sc)
            scenario_results.append(result)

        breakpoints = self.detect_liquidity_breakpoints(scenario_results)
        cost_curve_data = self.cost_curve(scenario_results)
        best_notional = self.best_research_notional(scenario_results)

        warnings = []
        if breakpoints:
            warnings.append("Liquidity breakpoints detected. Portfolio may be constrained at higher notionals.")

        return CapitalScalingResult(
            scaling_id=str(uuid.uuid4()),
            base_symbols=base_request.symbols,
            notionals=notionals,
            scenario_results=scenario_results,
            capacity_warnings=[bp["message"] for bp in breakpoints],
            estimated_cost_curve=cost_curve_data,
            liquidity_breakpoints=breakpoints,
            best_research_notional=best_notional,
            warnings=warnings
        )

    def build_notional_scenarios(self, notionals: list[float]) -> list[WhatIfScenario]:
        scenarios = []
        for n in notionals:
            if n <= 0:
                continue
            scenarios.append(WhatIfScenario(
                scenario_id=str(uuid.uuid4()),
                scenario_type=WhatIfScenarioType.CAPITAL_SCALE,
                name=f"Scale to {int(n)}",
                description=f"Scaling notional to {n}",
                assumptions=[
                    WhatIfAssumptionOverride(
                        override_id=str(uuid.uuid4()),
                        assumption_type=AssumptionType.PORTFOLIO_NOTIONAL,
                        name=f"Notional {n}",
                        old_value=None,
                        new_value=n,
                        description=f"Portfolio notional overridden to {n}"
                    )
                ]
            ))
        return scenarios

    def detect_liquidity_breakpoints(self, results: list[WhatIfScenarioResult]) -> list[dict[str, Any]]:
        breakpoints = []
        baseline_cost = None
        for res in results:
            # We look for a jump in estimated_total_cost_bps
            current_cost = res.estimated_total_cost_bps
            if current_cost is not None:
                if baseline_cost is not None and current_cost > baseline_cost * 1.5:
                    breakpoints.append({
                        "scenario_name": res.scenario.name,
                        "cost": current_cost,
                        "message": f"Sharp cost increase at {res.scenario.name}."
                    })
                baseline_cost = current_cost
        return breakpoints

    def cost_curve(self, results: list[WhatIfScenarioResult]) -> list[dict[str, Any]]:
        curve = []
        for res in results:
            notional = next((a.new_value for a in res.scenario.assumptions if a.assumption_type == AssumptionType.PORTFOLIO_NOTIONAL), None)
            if notional is not None:
                curve.append({
                    "notional": notional,
                    "estimated_total_cost_bps": res.estimated_total_cost_bps
                })
        return curve

    def best_research_notional(self, results: list[WhatIfScenarioResult]) -> float | None:
        best_notional = None
        best_score = -1.0
        for res in results:
            score = res.estimated_net_quality_score or 0.0
            if score > best_score:
                best_score = score
                notional = next((a.new_value for a in res.scenario.assumptions if a.assumption_type == AssumptionType.PORTFOLIO_NOTIONAL), None)
                if notional is not None:
                    best_notional = notional
        return best_notional
