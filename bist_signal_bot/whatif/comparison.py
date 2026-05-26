import uuid
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.whatif.models import (
    WhatIfScenarioResult, WhatIfScenarioType, WhatIfComparisonResult, SensitivityFinding
)

class WhatIfComparisonEngine:
    def __init__(self, settings: Settings, logger: Any):
        self.settings = settings
        self.logger = logger

    def compare(self, results: list[WhatIfScenarioResult]) -> WhatIfComparisonResult:
        baseline_result = next((r for r in results if r.scenario.scenario_type == WhatIfScenarioType.BASELINE), None)
        baseline_id = baseline_result.result_id if baseline_result else None

        ranking = self.rank_scenarios(results)
        best_id = self.best_scenario(results)
        worst_id = self.worst_scenario(results)

        comp = WhatIfComparisonResult(
            comparison_id=str(uuid.uuid4()),
            baseline_result_id=baseline_id,
            scenario_results=results,
            best_scenario_id=best_id,
            worst_scenario_id=worst_id,
            sensitivity_findings=[], # Injected externally by WhatIfEngine
            ranking=ranking,
            key_findings=[], # Populated later
            warnings=[]
        )
        comp.key_findings = self.key_findings(comp)
        return comp

    def rank_scenarios(self, results: list[WhatIfScenarioResult]) -> list[dict[str, Any]]:
        metric = getattr(self.settings, "WHATIF_RANKING_METRIC", "estimated_net_quality_score")
        valid_results = [(r, getattr(r, metric, 0.0) or 0.0) for r in results]
        valid_results.sort(key=lambda x: x[1], reverse=True)
        return [{"scenario_id": r.result_id, "scenario_name": r.scenario.name, metric: score} for r, score in valid_results]

    def best_scenario(self, results: list[WhatIfScenarioResult]) -> str | None:
        ranked = self.rank_scenarios(results)
        return ranked[0]["scenario_id"] if ranked else None

    def worst_scenario(self, results: list[WhatIfScenarioResult]) -> str | None:
        ranked = self.rank_scenarios(results)
        return ranked[-1]["scenario_id"] if ranked else None

    def key_findings(self, comparison: WhatIfComparisonResult) -> list[str]:
        findings = []
        if comparison.best_scenario_id:
            best_r = next((r for r in comparison.scenario_results if r.result_id == comparison.best_scenario_id), None)
            if best_r:
                findings.append(f"Scenario '{best_r.scenario.name}' is research-favorable under current assumptions.")

        if comparison.worst_scenario_id:
            worst_r = next((r for r in comparison.scenario_results if r.result_id == comparison.worst_scenario_id), None)
            if worst_r:
                findings.append(f"Scenario '{worst_r.scenario.name}' significantly reduces portfolio quality.")

        return findings
