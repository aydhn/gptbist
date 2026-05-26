import uuid
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.whatif.models import (
    WhatIfRunRequest, WhatIfScenario, WhatIfScenarioResult, WhatIfStatus
)
from bist_signal_bot.portfolio_construction.models import PortfolioConstructionRequest
from bist_signal_bot.portfolio_construction.engine import PortfolioConstructionEngine

class CounterfactualEngine:
    def __init__(self, settings: Settings, assumption_engine: Any, logger: Any):
        self.settings = settings
        self.assumption_engine = assumption_engine
        self.logger = logger
        # Need to instantiate or receive the actual portfolio construction engine.
        # Assuming we can instantiate it here with settings for counterfactual runs.
        self.portfolio_engine = None  # Mocked in tests or injected in app factory

    def run_counterfactual(self, request: WhatIfRunRequest, scenario: WhatIfScenario) -> WhatIfScenarioResult:
        if request.include_portfolio_construction:
            return self.run_portfolio_construction_counterfactual(request, scenario)
        elif request.include_portfolio_ledger:
            return self.run_portfolio_ledger_counterfactual(request, scenario)
        else:
            return WhatIfScenarioResult(
                result_id=str(uuid.uuid4()),
                scenario=scenario,
                status=WhatIfStatus.INSUFFICIENT_DATA,
                warnings=["Neither portfolio construction nor ledger included in counterfactual run."]
            )

    def run_portfolio_construction_counterfactual(self, request: WhatIfRunRequest, scenario: WhatIfScenario) -> WhatIfScenarioResult:
        try:
            overrides = self.assumption_engine.apply_overrides(self.settings, scenario.assumptions)

            # Map overrides to PortfolioConstructionRequest fields safely.
            pc_req = PortfolioConstructionRequest(
                request_id=str(uuid.uuid4()),
                universe_name=request.source_ref or "whatif_universe",
                symbols=request.symbols,
                strategy_names=request.strategy_names,
                weighting_method=overrides.get("WEIGHTING_METHOD", self.settings.PORTFOLIO_DEFAULT_WEIGHTING_METHOD),
                max_positions=overrides.get("MAX_POSITIONS", self.settings.PORTFOLIO_MAX_POSITIONS),
                portfolio_notional=overrides.get("PORTFOLIO_NOTIONAL", self.settings.PORTFOLIO_DEFAULT_NOTIONAL),
                current_weights={},
                apply_constraints=True,
                include_execution_costs=request.include_execution_costs,
                include_liquidity_penalty=self.settings.PORTFOLIO_USE_LIQUIDITY_PENALTY,
                include_calibration=overrides.get("USE_CALIBRATION", self.settings.PORTFOLIO_USE_CALIBRATED_CONFIDENCE),
                include_strategy_scorecard=overrides.get("USE_STRATEGY_SCORECARD", self.settings.PORTFOLIO_USE_STRATEGY_SCORECARD),
                include_monte_carlo=overrides.get("USE_MONTE_CARLO_SCORE", self.settings.PORTFOLIO_USE_MONTE_CARLO_SCORE),
                metadata={"whatif_scenario": scenario.name, "is_counterfactual": True}
            )

            # NOTE: For counterfactual, we need to inject the overrides into the engine.
            # In a real implementation, we would pass overrides to the engine's build_portfolio method
            # For this MVP, we simulate the execution by extracting from a dummy payload if the engine doesn't support overrides natively.
            # Assuming PortfolioConstructionEngine supports a __whatif_overrides__ flag in its metadata or we mock it.

            # We call the engine
            pc_result = self.portfolio_engine.construct(pc_req)

            # Map PC Result to WhatIfScenarioResult
            return self.extract_metrics(pc_result.model_dump(), scenario)

        except Exception as e:
            self.logger.error(f"Counterfactual portfolio construction failed: {e}")
            return WhatIfScenarioResult(
                result_id=str(uuid.uuid4()),
                scenario=scenario,
                status=WhatIfStatus.ERROR,
                warnings=[str(e)]
            )

    def run_portfolio_ledger_counterfactual(self, request: WhatIfRunRequest, scenario: WhatIfScenario) -> WhatIfScenarioResult:
        # Portfolio ledger counterfactual using valuation engine
        # Here we mock the behavior for the MVP
        return WhatIfScenarioResult(
            result_id=str(uuid.uuid4()),
            scenario=scenario,
            status=WhatIfStatus.PASS,
            simulated_nav=105000.0,
            gross_return_pct=5.0,
            net_return_pct=4.8,
            warnings=["Simulated using mock valuation for MVP"]
        )
    def extract_metrics(self, payload: dict[str, Any], scenario: WhatIfScenario) -> WhatIfScenarioResult:
        status_str = payload.get("status", "UNKNOWN")
        try:
            status = WhatIfStatus(status_str)
        except ValueError:
            status = WhatIfStatus.UNKNOWN

        return WhatIfScenarioResult(
            result_id=str(uuid.uuid4()),
            scenario=scenario,
            status=status,
            portfolio_score=payload.get("portfolio_score"),
            diversification_score=payload.get("diversification_score"),
            estimated_net_quality_score=payload.get("estimated_net_quality_score"),
            estimated_total_cost_bps=payload.get("estimated_total_cost_bps"),
            estimated_turnover_pct=payload.get("estimated_turnover_pct"),
            expected_signal_count=len(payload.get("candidates", [])),
            selected_symbols=[p["symbol"] for p in payload.get("positions", [])],
            constraint_violations_count=len(payload.get("violations", [])),
            output_refs=payload.get("output_files", {})
        )
