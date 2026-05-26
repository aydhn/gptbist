import time
import uuid
from pathlib import Path
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.whatif.models import (
    WhatIfRunRequest, WhatIfRunResult, WhatIfStatus, WhatIfScenarioType, AssumptionType,
    CapitalScalingResult, PolicySandboxResult
)
from bist_signal_bot.whatif.scenarios import WhatIfScenarioFactory
from bist_signal_bot.whatif.assumptions import AssumptionOverrideEngine
from bist_signal_bot.whatif.counterfactual import CounterfactualEngine
from bist_signal_bot.whatif.comparison import WhatIfComparisonEngine
from bist_signal_bot.whatif.sensitivity import SensitivityAnalyzer
from bist_signal_bot.whatif.capital_scaling import CapitalScalingAnalyzer
from bist_signal_bot.whatif.policy_sandbox import PolicySandbox
from bist_signal_bot.whatif.storage import WhatIfStore

class WhatIfEngine:
    def __init__(
        self,
        scenario_factory: WhatIfScenarioFactory,
        assumption_engine: AssumptionOverrideEngine,
        counterfactual_engine: CounterfactualEngine,
        comparison_engine: WhatIfComparisonEngine,
        sensitivity_analyzer: SensitivityAnalyzer,
        capital_scaling_analyzer: CapitalScalingAnalyzer,
        policy_sandbox: PolicySandbox,
        store: WhatIfStore,
        settings: Settings,
        logger: Any
    ):
        self.scenario_factory = scenario_factory
        self.assumption_engine = assumption_engine
        self.counterfactual_engine = counterfactual_engine
        self.comparison_engine = comparison_engine
        self.sensitivity_analyzer = sensitivity_analyzer
        self.capital_scaling_analyzer = capital_scaling_analyzer
        self.policy_sandbox = policy_sandbox
        self.store = store
        self.settings = settings
        self.logger = logger

    def run(self, request: WhatIfRunRequest) -> WhatIfRunResult:
        start_time = time.time()
        self.logger.info(f"Starting What-If run for source {request.source_type}")

        scenario_results = []

        # 1. Baseline
        baseline_scenarios = [s for s in request.scenarios if s.scenario_type == WhatIfScenarioType.BASELINE]
        if request.baseline_required and not baseline_scenarios:
            baseline_scenarios = [self.scenario_factory.baseline()]

        for sc in baseline_scenarios:
            res = self.counterfactual_engine.run_counterfactual(request, sc)
            scenario_results.append(res)

        baseline_result = scenario_results[0] if scenario_results else None

        # 2. Scenarios
        other_scenarios = [s for s in request.scenarios if s.scenario_type != WhatIfScenarioType.BASELINE]
        for sc in other_scenarios:
            if not sc.enabled:
                continue
            res = self.counterfactual_engine.run_counterfactual(request, sc)
            scenario_results.append(res)

        # 3. Comparison
        comparison = self.comparison_engine.compare(scenario_results)

        # 4. Sensitivity
        if baseline_result:
            findings = self.sensitivity_analyzer.analyze(baseline_result, scenario_results)
            comparison.sensitivity_findings = findings

        # 5. Capital Scaling
        capital_scaling = None
        if getattr(self.settings, "WHATIF_INCLUDE_CAPITAL_SCALING", True):
            notionals_str = getattr(self.settings, "WHATIF_CAPITAL_SCALE_NOTIONALS", "50000,100000,250000,500000")
            notionals = [float(n) for n in str(notionals_str).split(",") if n.strip()]
            capital_scaling = self.capital_scaling_analyzer.run_scaling(request, notionals)

        # 6. Policy Sandbox
        policy_sandbox = None
        if getattr(self.settings, "WHATIF_INCLUDE_POLICY_SANDBOX", False):
            # Example policies
            policies = [
                {"name": "conservative-liquidity", "LIQUIDITY_FILTER": True, "CONFIDENCE_THRESHOLD": 80},
                {"name": "high-confidence-only", "CONFIDENCE_THRESHOLD": 85}
            ]
            policy_sandbox = self.policy_sandbox.test_policy_set("Built-in Presets", policies, request)

        status = WhatIfStatus.PASS
        if any(r.status == WhatIfStatus.ERROR for r in scenario_results):
            status = WhatIfStatus.ERROR

        run_result = WhatIfRunResult(
            run_id=str(uuid.uuid4()),
            request=request,
            elapsed_seconds=time.time() - start_time,
            status=status,
            scenario_results=scenario_results,
            comparison=comparison,
            capital_scaling=capital_scaling,
            policy_sandbox=policy_sandbox,
        )

        if request.save_output:
            try:
                paths = self.store.save_run(run_result)
                run_result.output_files = {k: str(v) for k, v in paths.items()}
            except Exception as e:
                self.logger.error(f"Failed to save What-If run output: {e}")
                run_result.warnings.append(f"Storage error: {e}")

        # In a real implementation, you'd publish an audit event here:
        # self.audit_log("WHATIF_RUN_COMPLETED", metadata={"run_id": run_result.run_id})

        return run_result

    def run_default(self, source_type: str, source_ref: str | None = None) -> WhatIfRunResult:
        scenarios = self.scenario_factory.default_scenarios()
        req = WhatIfRunRequest(
            request_id=str(uuid.uuid4()),
            source_type=source_type,
            source_ref=source_ref,
            scenarios=scenarios
        )
        return self.run(req)

    def run_sensitivity(self, source_type: str, source_ref: str | None, assumption_type: AssumptionType) -> WhatIfRunResult:
        # Runs baseline and a set of variations for a single assumption
        scenarios = [self.scenario_factory.baseline()]
        # Fake variation scenarios depending on the assumption for the MVP
        if assumption_type == AssumptionType.COMMISSION_BPS:
            scenarios.extend([self.scenario_factory.cost_stress(1.5), self.scenario_factory.cost_stress(2.0)])
        elif assumption_type == AssumptionType.CONFIDENCE_THRESHOLD:
            scenarios.extend([self.scenario_factory.threshold_change(70.0), self.scenario_factory.threshold_change(80.0)])
        else:
            scenarios.append(self.scenario_factory.constraint_change("Var1", assumption_type, 1.0))

        req = WhatIfRunRequest(
            request_id=str(uuid.uuid4()),
            source_type=source_type,
            source_ref=source_ref,
            scenarios=scenarios
        )
        return self.run(req)

    def run_capital_scale(self, source_type: str, source_ref: str | None, notionals: list[float]) -> CapitalScalingResult:
        req = WhatIfRunRequest(
            request_id=str(uuid.uuid4()),
            source_type=source_type,
            source_ref=source_ref,
            scenarios=[self.scenario_factory.baseline()]
        )
        return self.capital_scaling_analyzer.run_scaling(req, notionals)

    def run_policy_sandbox(self, source_type: str, source_ref: str | None, policies: list[dict[str, Any]]) -> PolicySandboxResult:
        req = WhatIfRunRequest(
            request_id=str(uuid.uuid4()),
            source_type=source_type,
            source_ref=source_ref,
            scenarios=[self.scenario_factory.baseline()]
        )
        return self.policy_sandbox.test_policy_set("Custom CLI Policies", policies, req)
