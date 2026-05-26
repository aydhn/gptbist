import uuid
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.whatif.models import (
    WhatIfRunRequest, PolicySandboxResult, WhatIfScenarioResult, WhatIfScenario,
    WhatIfScenarioType, AssumptionType, WhatIfAssumptionOverride
)

class PolicySandbox:
    def __init__(self, settings: Settings, counterfactual_engine: Any, logger: Any):
        self.settings = settings
        self.counterfactual_engine = counterfactual_engine
        self.logger = logger

    def test_policy_set(self, policy_name: str, policies: list[dict[str, Any]], base_request: WhatIfRunRequest) -> PolicySandboxResult:
        scenario_results = []
        for p in policies:
            sc = self.policy_to_scenario(p)
            res = self.counterfactual_engine.run_counterfactual(base_request, sc)
            scenario_results.append(res)

        candidate = self.select_candidate_policy(scenario_results)

        return PolicySandboxResult(
            sandbox_id=str(uuid.uuid4()),
            policy_name=policy_name,
            policy_description=f"Testing policy preset: {policy_name}",
            baseline_policy={},
            tested_policies=policies,
            scenario_results=scenario_results,
            selected_policy_candidate=candidate
        )

    def policy_to_scenario(self, policy: dict[str, Any]) -> WhatIfScenario:
        assumptions = []
        for k, v in policy.items():
            try:
                a_type = AssumptionType(k)
            except ValueError:
                a_type = AssumptionType.CUSTOM

            assumptions.append(WhatIfAssumptionOverride(
                override_id=str(uuid.uuid4()),
                assumption_type=a_type,
                name=f"Policy {k}",
                old_value=None,
                new_value=v,
                description=f"Policy setting {k} = {v}"
            ))

        return WhatIfScenario(
            scenario_id=str(uuid.uuid4()),
            scenario_type=WhatIfScenarioType.CUSTOM,
            name=f"Policy {policy.get('name', 'candidate')}",
            description="Policy sandbox candidate.",
            assumptions=assumptions
        )

    def rank_policies(self, results: list[WhatIfScenarioResult]) -> list[dict[str, Any]]:
        metric = getattr(self.settings, "WHATIF_RANKING_METRIC", "estimated_net_quality_score")
        valid_results = [(r, getattr(r, metric, 0.0) or 0.0) for r in results]
        valid_results.sort(key=lambda x: x[1], reverse=True)
        return [{"scenario_name": r.scenario.name, metric: score} for r, score in valid_results]

    def select_candidate_policy(self, results: list[WhatIfScenarioResult]) -> dict[str, Any] | None:
        ranked = self.rank_policies(results)
        if not ranked:
            return None
        best_name = ranked[0]["scenario_name"]
        for r in results:
            if r.scenario.name == best_name:
                policy = {"name": best_name}
                for a in r.scenario.assumptions:
                    policy[a.assumption_type.value] = a.new_value
                return policy
        return None
