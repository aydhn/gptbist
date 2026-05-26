import uuid
from typing import Any
from bist_signal_bot.whatif.models import (
    WhatIfScenario, WhatIfScenarioType, AssumptionType, WhatIfAssumptionOverride
)

class WhatIfScenarioFactory:

    def default_scenarios(self) -> list[WhatIfScenario]:
        return [
            self.baseline(),
            self.cost_stress(1.5),
            self.cost_stress(2.0),
            self.slippage_stress(1.5),
            self.slippage_stress(2.0),
            self.liquidity_stress(),
            self.capital_scale(50000.0),
            self.capital_scale(100000.0),
            self.capital_scale(500000.0),
            self.constraint_change("Max positions 5", AssumptionType.MAX_POSITIONS, 5),
            self.constraint_change("Max positions 10", AssumptionType.MAX_POSITIONS, 10),
            self.threshold_change(70.0),
            self.threshold_change(80.0),
            self.constraint_change("Max sector weight 25%", AssumptionType.MAX_SECTOR_WEIGHT, 0.25),
            self.constraint_change("Max symbol weight 15%", AssumptionType.MAX_SYMBOL_WEIGHT, 0.15),
            self.toggle_change("Calibration off", AssumptionType.USE_CALIBRATION, False),
            self.toggle_change("Strategy scorecard off", AssumptionType.USE_STRATEGY_SCORECARD, False),
            self.toggle_change("Monte Carlo score off", AssumptionType.USE_MONTE_CARLO_SCORE, False),
        ]

    def baseline(self) -> WhatIfScenario:
        return WhatIfScenario(
            scenario_id=str(uuid.uuid4()),
            scenario_type=WhatIfScenarioType.BASELINE,
            name="Baseline",
            description="Baseline scenario with current configurations",
            assumptions=[]
        )

    def scenario_by_name(self, name: str) -> WhatIfScenario | None:
        for sc in self.default_scenarios():
            if sc.name == name:
                return sc
        return None

    def cost_stress(self, multiplier: float) -> WhatIfScenario:
        pct = int((multiplier - 1.0) * 100)
        return WhatIfScenario(
            scenario_id=str(uuid.uuid4()),
            scenario_type=WhatIfScenarioType.COST_STRESS,
            name=f"Cost +{pct}%",
            description=f"Stress scenario simulating {multiplier}x trading costs.",
            assumptions=[
                WhatIfAssumptionOverride(
                    override_id=str(uuid.uuid4()),
                    assumption_type=AssumptionType.COMMISSION_BPS,
                    name=f"Cost Multiplier {multiplier}x",
                    old_value=None,
                    new_value=multiplier,
                    description=f"Apply a {multiplier}x multiplier to baseline commission."
                )
            ]
        )

    def slippage_stress(self, multiplier: float) -> WhatIfScenario:
        pct = int((multiplier - 1.0) * 100)
        return WhatIfScenario(
            scenario_id=str(uuid.uuid4()),
            scenario_type=WhatIfScenarioType.SLIPPAGE_STRESS,
            name=f"Slippage +{pct}%",
            description=f"Stress scenario simulating {multiplier}x slippage.",
            assumptions=[
                WhatIfAssumptionOverride(
                    override_id=str(uuid.uuid4()),
                    assumption_type=AssumptionType.SLIPPAGE_BPS,
                    name=f"Slippage Multiplier {multiplier}x",
                    old_value=None,
                    new_value=multiplier,
                    description=f"Apply a {multiplier}x multiplier to baseline slippage."
                )
            ]
        )

    def liquidity_stress(self) -> WhatIfScenario:
        return WhatIfScenario(
            scenario_id=str(uuid.uuid4()),
            scenario_type=WhatIfScenarioType.LIQUIDITY_STRESS,
            name="Liquidity stress",
            description="Stress scenario enforcing strict liquidity filters.",
            assumptions=[
                WhatIfAssumptionOverride(
                    override_id=str(uuid.uuid4()),
                    assumption_type=AssumptionType.LIQUIDITY_FILTER,
                    name="Strict Liquidity",
                    old_value=False,
                    new_value=True,
                    description="Require strict liquidity levels."
                )
            ]
        )

    def capital_scale(self, notional: float) -> WhatIfScenario:
        return WhatIfScenario(
            scenario_id=str(uuid.uuid4()),
            scenario_type=WhatIfScenarioType.CAPITAL_SCALE,
            name=f"Portfolio notional {int(notional/1000)}k",
            description=f"Scenario assuming a portfolio size of {notional}.",
            assumptions=[
                WhatIfAssumptionOverride(
                    override_id=str(uuid.uuid4()),
                    assumption_type=AssumptionType.PORTFOLIO_NOTIONAL,
                    name=f"Notional {notional}",
                    old_value=None,
                    new_value=notional,
                    description=f"Scale portfolio notional to {notional}."
                )
            ]
        )

    def threshold_change(self, threshold: float) -> WhatIfScenario:
        return WhatIfScenario(
            scenario_id=str(uuid.uuid4()),
            scenario_type=WhatIfScenarioType.THRESHOLD_CHANGE,
            name=f"Confidence threshold {int(threshold)}",
            description=f"Scenario requiring a minimum confidence threshold of {threshold}.",
            assumptions=[
                WhatIfAssumptionOverride(
                    override_id=str(uuid.uuid4()),
                    assumption_type=AssumptionType.CONFIDENCE_THRESHOLD,
                    name=f"Threshold {threshold}",
                    old_value=None,
                    new_value=threshold,
                    description=f"Set confidence threshold to {threshold}."
                )
            ]
        )

    def constraint_change(self, name: str, assumption_type: AssumptionType, value: Any) -> WhatIfScenario:
        return WhatIfScenario(
            scenario_id=str(uuid.uuid4()),
            scenario_type=WhatIfScenarioType.CONSTRAINT_CHANGE,
            name=name,
            description=f"Scenario applying constraint {name}.",
            assumptions=[
                WhatIfAssumptionOverride(
                    override_id=str(uuid.uuid4()),
                    assumption_type=assumption_type,
                    name=name,
                    old_value=None,
                    new_value=value,
                    description=f"Apply override {name} with value {value}."
                )
            ]
        )

    def toggle_change(self, name: str, assumption_type: AssumptionType, value: bool) -> WhatIfScenario:
        scen_type = {
            AssumptionType.USE_CALIBRATION: WhatIfScenarioType.CALIBRATION_TOGGLE,
            AssumptionType.USE_STRATEGY_SCORECARD: WhatIfScenarioType.STRATEGY_SCORE_TOGGLE,
            AssumptionType.USE_MONTE_CARLO_SCORE: WhatIfScenarioType.MONTE_CARLO_TOGGLE
        }.get(assumption_type, WhatIfScenarioType.CUSTOM)
        return WhatIfScenario(
            scenario_id=str(uuid.uuid4()),
            scenario_type=scen_type,
            name=name,
            description=f"Toggle {assumption_type.value} to {value}.",
            assumptions=[
                WhatIfAssumptionOverride(
                    override_id=str(uuid.uuid4()),
                    assumption_type=assumption_type,
                    name=name,
                    old_value=not value,
                    new_value=value,
                    description=f"Toggle {assumption_type.value} to {value}."
                )
            ]
        )
