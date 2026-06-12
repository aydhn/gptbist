import uuid
import logging
from typing import Any
from pathlib import Path

from bist_signal_bot.stress.models import (
    StressTestRequest,
    StressTestResult,
    StressStatus,
    StressSeverity,
    StressInputType,
    ReturnSeries
)
from bist_signal_bot.stress.returns import ReturnSeriesBuilder
from bist_signal_bot.stress.monte_carlo import MonteCarloSimulator
from bist_signal_bot.stress.shocks import ShockScenarioEngine
from bist_signal_bot.stress.drawdown import DrawdownSimulator
from bist_signal_bot.stress.risk_of_ruin import RiskOfRuinEstimator
from bist_signal_bot.stress.storage import StressStore
from bist_signal_bot.stress.reporting import format_stress_report_markdown

class StressTestEngine:
    def __init__(
        self,
        return_builder: ReturnSeriesBuilder,
        monte_carlo_simulator: MonteCarloSimulator,
        shock_engine: ShockScenarioEngine,
        drawdown_simulator: DrawdownSimulator,
        risk_of_ruin_estimator: RiskOfRuinEstimator,
        portfolio_research_engine: Any = None,
        data_service: Any = None,
        store: StressStore | None = None,
        settings: Any = None
    ):
        self.return_builder = return_builder
        self.monte_carlo_simulator = monte_carlo_simulator
        self.shock_engine = shock_engine
        self.drawdown_simulator = drawdown_simulator
        self.risk_of_ruin_estimator = risk_of_ruin_estimator
        self.portfolio_research_engine = portfolio_research_engine
        self.data_service = data_service
        self.store = store or StressStore()
        self.settings = settings
        self.logger = logging.getLogger("bist_signal_bot.stress.engine")

    def _prepare_inputs(self, request: StressTestRequest) -> tuple[Any, Any]:
        series = None
        snapshot = None

        if request.input_type == StressInputType.PORTFOLIO_RESEARCH_SNAPSHOT:
            if not self.portfolio_research_engine:
                raise ValueError("Portfolio research engine not provided.")
            if request.snapshot_id:
                snapshot = self.portfolio_research_engine.store.load_snapshot(request.snapshot_id)
            else:
                snapshot = self.portfolio_research_engine.store.load_latest_snapshot()

            if not snapshot:
                raise ValueError("No portfolio snapshot found.")

            symbols = [item.symbol for item in snapshot.items] if hasattr(snapshot, "items") else []
            if self.data_service and symbols:
                data_by_symbol = {sym: self.data_service.get_historical_data(sym) for sym in symbols}
            else:
                data_by_symbol = {}

            series = self.return_builder.from_portfolio_snapshot(snapshot, data_by_symbol)

        elif request.input_type == StressInputType.CUSTOM_RETURNS:
            if "custom_returns" in request.metadata:
                series = ReturnSeries(
                    series_id=str(uuid.uuid4()),
                    source_type=StressInputType.CUSTOM_RETURNS,
                    returns=request.metadata["custom_returns"],
                    frequency=request.timeframe
                )
            else:
                 raise ValueError("Custom returns must be provided in metadata.")
        else:
             raise NotImplementedError(f"Input type {request.input_type} not yet implemented.")

        return series, snapshot

    def _run_shocks(self, request: StressTestRequest, snapshot: Any) -> tuple[list, StressStatus]:
        shock_results = []
        status = StressStatus.PASS
        if request.include_shock_scenarios:
            scenarios = request.scenarios or self.shock_engine.default_scenarios()
            for sc in scenarios:
                res = self.shock_engine.apply_scenario(snapshot, sc)
                shock_results.append(res)
                if res.status in (StressStatus.FAIL, StressStatus.ERROR):
                    status = StressStatus.WARN
        return shock_results, status

    def _run_monte_carlo(self, request: StressTestRequest, series: ReturnSeries) -> tuple[Any, StressStatus]:
        mc_result = None
        status = StressStatus.PASS
        if request.include_monte_carlo:
            mc_result = self.monte_carlo_simulator.run(series, request.monte_carlo_config)
            if mc_result.status in (StressStatus.FAIL, StressStatus.ERROR):
                status = StressStatus.WARN
        return mc_result, status

    def _run_drawdown(self, request: StressTestRequest, series: ReturnSeries) -> Any:
        if request.include_drawdown:
            return self.drawdown_simulator.analyze(series)
        return None

    def _run_risk_of_ruin(self, request: StressTestRequest, series: ReturnSeries, mc_result: Any) -> tuple[Any, StressStatus]:
        ror_result = None
        status = StressStatus.PASS
        if request.include_risk_of_ruin:
            ror_result = self.risk_of_ruin_estimator.estimate(series, mc_result, request.ruin_threshold_pct)
            if ror_result.status == StressStatus.FAIL:
                status = StressStatus.FAIL
        return ror_result, status

    def _save_output(self, request: StressTestRequest, result_pre: StressTestResult) -> None:
        if request.save_output:
            try:
                paths = self.store.save_result(result_pre)
                result_pre.output_files = {k: str(v) for k, v in paths.items()}

                md_path = paths["result_json"].parent / "stress_report.md"
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(format_stress_report_markdown(result_pre))
                result_pre.output_files["report_md"] = str(md_path)
            except Exception as e:
                self.logger.error(f"Failed to save stress output: {e}")
                result_pre.warnings.append(f"Failed to save output: {e}")

    def run(self, request: StressTestRequest) -> StressTestResult:
        stress_id = str(uuid.uuid4())
        warnings = []
        status = StressStatus.PASS

        try:
            series, snapshot = self._prepare_inputs(request)
        except Exception as e:
            self.logger.error(f"Error preparing input: {e}")
            return StressTestResult(
                stress_id=stress_id,
                request=request,
                status=StressStatus.ERROR,
                stress_rating=StressSeverity.EXTREME,
                warnings=[f"Failed to prepare input: {e}"]
            )

        if not series or not series.returns:
             return StressTestResult(
                 stress_id=stress_id,
                 request=request,
                 status=StressStatus.ERROR,
                 stress_rating=StressSeverity.EXTREME,
                 warnings=["No returns available for stress test."]
             )

        shock_results, shock_status = self._run_shocks(request, snapshot)
        if shock_status == StressStatus.WARN:
            status = StressStatus.WARN

        mc_result, mc_status = self._run_monte_carlo(request, series)
        if mc_status == StressStatus.WARN:
            status = StressStatus.WARN

        dd_result = self._run_drawdown(request, series)

        ror_result, ror_status = self._run_risk_of_ruin(request, series, mc_result)
        if ror_status == StressStatus.FAIL:
            status = StressStatus.FAIL

        result_pre = StressTestResult(
            stress_id=stress_id,
            request=request,
            status=status,
            monte_carlo_result=mc_result,
            shock_results=shock_results,
            drawdown_result=dd_result,
            risk_of_ruin_result=ror_result,
            stress_rating=StressSeverity.MEDIUM, # Temp
            warnings=warnings
        )

        score = self.calculate_stress_score(result_pre)
        rating = self.rating_from_score(score)

        if rating == StressSeverity.EXTREME:
            status = StressStatus.FAIL
        elif rating == StressSeverity.HIGH:
            if status != StressStatus.FAIL:
                status = StressStatus.WARN

        result_pre.stress_score = score
        result_pre.stress_rating = rating
        result_pre.status = status

        self._save_output(request, result_pre)

        return result_pre

    def run_for_latest_portfolio(self, save_output: bool = True) -> StressTestResult:
        # Create a default request for the latest portfolio
        from bist_signal_bot.stress.models import MonteCarloConfig, MonteCarloMethod
        req = StressTestRequest(
            input_type=StressInputType.PORTFOLIO_RESEARCH_SNAPSHOT,
            monte_carlo_config=MonteCarloConfig(
                method=MonteCarloMethod.BOOTSTRAP,
                simulations=1000,
                horizon_days=60,
                seed=42,
                initial_value=100000.0
            ),
            ruin_threshold_pct=30.0,
            save_output=save_output
        )
        return self.run(req)

    def run_for_snapshot(self, snapshot_id: str, save_output: bool = True) -> StressTestResult:
        from bist_signal_bot.stress.models import MonteCarloConfig, MonteCarloMethod
        req = StressTestRequest(
            input_type=StressInputType.PORTFOLIO_RESEARCH_SNAPSHOT,
            snapshot_id=snapshot_id,
            monte_carlo_config=MonteCarloConfig(
                method=MonteCarloMethod.BOOTSTRAP,
                simulations=1000,
                horizon_days=60,
                seed=42,
                initial_value=100000.0
            ),
            ruin_threshold_pct=30.0,
            save_output=save_output
        )
        return self.run(req)

    def run_for_custom_returns(self, returns: list[float], save_output: bool = True) -> StressTestResult:
        from bist_signal_bot.stress.models import MonteCarloConfig, MonteCarloMethod
        req = StressTestRequest(
            input_type=StressInputType.CUSTOM_RETURNS,
            monte_carlo_config=MonteCarloConfig(
                method=MonteCarloMethod.BOOTSTRAP,
                simulations=1000,
                horizon_days=60,
                seed=42,
                initial_value=100000.0
            ),
            ruin_threshold_pct=30.0,
            save_output=save_output,
            metadata={"custom_returns": returns}
        )
        return self.run(req)

    def calculate_stress_score(self, result: StressTestResult) -> float:
        # Scale 0 to 100, where 100 is EXTREME STRESS (high risk)
        score = 0.0

        if result.risk_of_ruin_result and result.risk_of_ruin_result.estimated_ruin_probability_pct:
            rp = result.risk_of_ruin_result.estimated_ruin_probability_pct
            score += min(rp * 2, 40.0) # Up to 40 pts

        if result.monte_carlo_result and result.monte_carlo_result.max_drawdown_pct_p05:
            # Note: p05 drawdown is best case. Maybe we should use p95 for score.
            # Using p95 as the worst case
            mdd = abs(result.monte_carlo_result.max_drawdown_pct_p95 or 0.0)
            score += min(mdd * 1.5, 30.0) # Up to 30 pts

        if result.shock_results:
            worst_impact = min([r.estimated_portfolio_impact_pct or 0.0 for r in result.shock_results])
            if worst_impact < 0:
                score += min(abs(worst_impact), 20.0) # Up to 20 pts

        if result.warnings:
            score += min(len(result.warnings) * 2, 10.0)

        return min(max(score, 0.0), 100.0)

    def rating_from_score(self, score: float) -> StressSeverity:
        if score < 25.0:
            return StressSeverity.LOW
        elif score < 50.0:
            return StressSeverity.MEDIUM
        elif score < 75.0:
            return StressSeverity.HIGH
        else:
            return StressSeverity.EXTREME