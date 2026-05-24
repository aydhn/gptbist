from typing import Any
import uuid

from bist_signal_bot.execution_sim.models import ExecutionScenario, ExecutionScenarioType, SimulatedOrder, SimulatedFill

class ExecutionScenarioManager:
    def __init__(self, settings: Any | None = None):
        self.settings = settings

    def default_scenarios(self) -> list[ExecutionScenario]:
        return [
            ExecutionScenario(
                scenario_id=str(uuid.uuid4()),
                scenario_type=ExecutionScenarioType.OPTIMISTIC,
                name="Optimistic",
                cost_multiplier=0.5,
                slippage_multiplier=0.5,
                liquidity_haircut_pct=0.0,
                fill_probability_multiplier=1.2
            ),
            ExecutionScenario(
                scenario_id=str(uuid.uuid4()),
                scenario_type=ExecutionScenarioType.BASE,
                name="Base",
                cost_multiplier=1.0,
                slippage_multiplier=1.0,
                liquidity_haircut_pct=0.0,
                fill_probability_multiplier=1.0
            ),
            ExecutionScenario(
                scenario_id=str(uuid.uuid4()),
                scenario_type=ExecutionScenarioType.CONSERVATIVE,
                name="Conservative",
                cost_multiplier=1.5,
                slippage_multiplier=1.5,
                liquidity_haircut_pct=10.0,
                fill_probability_multiplier=0.8
            ),
            ExecutionScenario(
                scenario_id=str(uuid.uuid4()),
                scenario_type=ExecutionScenarioType.STRESS,
                name="Stress",
                cost_multiplier=2.0,
                slippage_multiplier=3.0,
                liquidity_haircut_pct=50.0,
                fill_probability_multiplier=0.5
            )
        ]

    def get_scenario(self, scenario_type: ExecutionScenarioType) -> ExecutionScenario:
        for s in self.default_scenarios():
            if s.scenario_type == scenario_type:
                return s
        return self.default_scenarios()[1] # Base default

    def apply_scenario_to_fill(self, fill: SimulatedFill, scenario: ExecutionScenario) -> SimulatedFill:
        # Actually in FillSimulator but here as a utility per design
        return fill

    def scenario_matrix(self, order: SimulatedOrder, price_df: Any) -> list[SimulatedFill]:
        # Typically handled via FillSimulator with multiple scenarios
        return []
