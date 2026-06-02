from typing import Any

import uuid
from .models import SyntheticScenarioSpec, SyntheticStressCase, SyntheticOutputKind

class SyntheticStressCaseBuilder:
    def default_stress_cases(self, spec: SyntheticScenarioSpec) -> list[SyntheticStressCase]:
        return [
            self.crash_stress(spec),
            self.liquidity_stress(spec),
            self.macro_stress(spec),
            self.schema_stress(spec)
        ]

    def crash_stress(self, spec: SyntheticScenarioSpec) -> SyntheticStressCase:
        return SyntheticStressCase(
            stress_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            stress_name="Crash Stress",
            description="Market crash scenario",
            affected_outputs=[SyntheticOutputKind.OHLCV, SyntheticOutputKind.PORTFOLIO_OUTCOMES],
            severity="HIGH",
            parameters={"drop": -0.2},
            expected_findings=["High drawdown expected"]
        )

    def liquidity_stress(self, spec: SyntheticScenarioSpec) -> SyntheticStressCase:
        return SyntheticStressCase(
            stress_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            stress_name="Liquidity Stress",
            description="Low liquidity scenario",
            affected_outputs=[SyntheticOutputKind.OHLCV],
            severity="MEDIUM",
            parameters={"volume_multiplier": 0.1},
            expected_findings=["Wide spreads expected"]
        )

    def macro_stress(self, spec: SyntheticScenarioSpec) -> SyntheticStressCase:
        return SyntheticStressCase(
            stress_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            stress_name="Macro Stress",
            description="Macro shock scenario",
            affected_outputs=[SyntheticOutputKind.MACRO],
            severity="HIGH",
            parameters={"rate_shock": 0.05},
            expected_findings=["High volatility expected"]
        )

    def schema_stress(self, spec: SyntheticScenarioSpec) -> SyntheticStressCase:
        return SyntheticStressCase(
            stress_id=str(uuid.uuid4()),
            scenario_id=spec.scenario_id,
            stress_name="Schema Stress",
            description="Schema changes",
            affected_outputs=[SyntheticOutputKind.OHLCV],
            severity="LOW",
            parameters={"extra_cols": 2},
            expected_findings=["Should not crash"]
        )

    def expected_findings(self, case: SyntheticStressCase) -> list[str]:
        return case.expected_findings
