import logging
import uuid
import time
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import MonteCarloValidationError

from .models import (
    MonteCarloRequest, MonteCarloResult, MonteCarloMetricType,
    MonteCarloTarget, ResamplingMethod
)
from .randomness import MonteCarloRandomState
from .resampling import ResamplingEngine
from .bootstrap import BootstrapEngine
from .path_simulation import PathSimulator
from .trade_simulation import TradeSimulationAdapter
from .cost_randomization import CostRandomizer
from .distributions import DistributionAnalyzer
from .reality_check import RealityCheckEngine
from .risk_metrics import MonteCarloRiskAnalyzer
from .scoring import MonteCarloRobustnessScorer
from .storage import MonteCarloStore

# ContextFusion collects monte carlo robustness
class MonteCarloEngine:
    def __init__(self,
                 trade_adapter: TradeSimulationAdapter | None = None,
                 bootstrap_engine: BootstrapEngine | None = None,
                 path_simulator: PathSimulator | None = None,
                 cost_randomizer: CostRandomizer | None = None,
                 distribution_analyzer: DistributionAnalyzer | None = None,
                 risk_analyzer: MonteCarloRiskAnalyzer | None = None,
                 reality_check: RealityCheckEngine | None = None,
                 scorer: MonteCarloRobustnessScorer | None = None,
                 store: MonteCarloStore | None = None,
                 settings: Settings | None = None,
                 logger: logging.Logger | None = None):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger("bist_signal_bot.monte_carlo")
        self.trade_adapter = trade_adapter or TradeSimulationAdapter(self.logger)
        self.bootstrap = bootstrap_engine or BootstrapEngine()
        self.path_simulator = path_simulator or PathSimulator()
        self.cost_randomizer = cost_randomizer or CostRandomizer()
        self.distribution = distribution_analyzer or DistributionAnalyzer()
        self.risk_analyzer = risk_analyzer or MonteCarloRiskAnalyzer()
        self.reality_check = reality_check or RealityCheckEngine(self.settings)
        self.scorer = scorer or MonteCarloRobustnessScorer()
        self.store = store or MonteCarloStore(self.settings)

    def run(self, request: MonteCarloRequest, backtest_result: Any | None = None, trades: list[dict[str, Any]] | None = None, returns: list[float] | None = None) -> MonteCarloResult:
        self.logger.info(f"Starting Monte Carlo simulation (Request ID: {request.request_id})")
        start_time = time.time()

        warnings = []
        errors = []

        try:
            active_trades = trades
            active_returns = returns
            observed_metric_value = None

            if request.target == MonteCarloTarget.BACKTEST_RESULT:
                if not backtest_result:
                    raise MonteCarloValidationError("Backtest result required for BACKTEST_RESULT target.")
                active_trades = self.trade_adapter.trades_from_backtest_result(backtest_result)
                active_returns = self.trade_adapter.returns_from_backtest_result(backtest_result, use_net=True)
                if hasattr(backtest_result, "metrics") and backtest_result.metrics:
                    observed_metric_value = backtest_result.metrics.get("net_total_return_pct")
                if not request.strategy_name and hasattr(backtest_result, "strategy_name"):
                    request.strategy_name = backtest_result.strategy_name
                if not request.symbol and hasattr(backtest_result, "symbol"):
                    request.symbol = backtest_result.symbol

            sample_size = len(active_trades) if active_trades else len(active_returns) if active_returns else 0
            size_warnings = self.bootstrap.validate_sample_size(sample_size, request.simulations)
            warnings.extend(size_warnings)

            if sample_size == 0:
                return self._create_insufficient_data_result(request, start_time, warnings)

            if active_trades and request.method in (ResamplingMethod.TRADE_BOOTSTRAP, ResamplingMethod.TRADE_SHUFFLE):
                sim_trades = self.bootstrap.bootstrap_trades(active_trades, request.simulations, request.seed, request.method)
                if request.include_cost_randomization or request.include_slippage_randomization:
                    cost_config = self.cost_randomizer.default_config(self.settings)
                    sim_trades = [self.cost_randomizer.randomize_trade_costs(st, cost_config, request.seed + i) for i, st in enumerate(sim_trades)]
                paths = self.path_simulator.simulate_paths_from_trades(sim_trades, request)
            else:
                ret_src = active_returns if active_returns else [t.get("net_return_pct", 0.0) for t in active_trades] if active_trades else []
                sim_returns = self.bootstrap.bootstrap_returns(ret_src, request.simulations, request.seed, request.method, request.block_size)
                if request.include_cost_randomization or request.include_slippage_randomization:
                    cost_config = self.cost_randomizer.default_config(self.settings)
                    sim_returns = [self.cost_randomizer.randomize_returns_for_costs(sr, cost_config, request.seed + i) for i, sr in enumerate(sim_returns)]
                paths = self.path_simulator.simulate_paths_from_returns(sim_returns, request)

            final_equities = [p.final_equity for p in paths]
            total_returns = [p.total_return_pct for p in paths]
            max_drawdowns = [p.max_drawdown_pct for p in paths]

            d_eq = self.distribution.build_distribution(MonteCarloMetricType.FINAL_EQUITY, final_equities)
            d_tr = self.distribution.build_distribution(MonteCarloMetricType.TOTAL_RETURN, total_returns, observed_value=observed_metric_value)
            d_mdd = self.distribution.build_distribution(MonteCarloMetricType.MAX_DRAWDOWN, max_drawdowns)

            distributions = [d_eq, d_tr, d_mdd]
            metrics = [self.distribution.summary_metric(d) for d in distributions]

            risk_summary = self.risk_analyzer.risk_summary(
                paths, request.initial_equity, request.ruin_threshold_pct, self.settings.MONTE_CARLO_DRAWDOWN_THRESHOLD_PCT
            )

            rc_result = None
            if request.include_reality_check:
                rc_result = self.reality_check.run(
                    observed_metric_value, total_returns, request.strategy_name, request.symbol, trials_count=1
                )

            score = self.scorer.score(risk_summary, rc_result, metrics)
            status = self.scorer.derive_status(score, warnings)
            actions = self.recommended_actions(score, risk_summary, rc_result)
            elapsed = time.time() - start_time

            result = MonteCarloResult(
                monte_carlo_id=str(uuid.uuid4()),
                request=request,
                status=status,
                elapsed_seconds=elapsed,
                paths=paths,
                metrics=metrics,
                distributions=distributions,
                risk_summary=risk_summary,
                reality_check=rc_result,
                robustness_score=score,
                recommended_actions=actions,
                warnings=warnings,
                errors=errors
            )

            if request.save_output and self.settings.MONTE_CARLO_SAVE_RESULTS:
                output_files = self.store.save_result(result)
                result.output_files = {k: str(v) for k, v in output_files.items()}

            self.logger.info(f"Monte Carlo simulation completed (ID: {result.monte_carlo_id}, Status: {status.value})")
            return result

        except Exception as e:
            self.logger.exception("Error during Monte Carlo simulation")
            return self._create_error_result(request, start_time, [str(e)])

    def run_from_backtest(self, backtest_result: Any, request: MonteCarloRequest) -> MonteCarloResult:
        request.target = MonteCarloTarget.BACKTEST_RESULT
        return self.run(request, backtest_result=backtest_result)

    def run_from_trades(self, trades: list[dict[str, Any]], request: MonteCarloRequest) -> MonteCarloResult:
        request.target = MonteCarloTarget.TRADES
        return self.run(request, trades=trades)

    def run_from_returns(self, returns: list[float], request: MonteCarloRequest) -> MonteCarloResult:
        request.target = MonteCarloTarget.RETURNS
        return self.run(request, returns=returns)

    def recommended_actions(self, score: float | None, risk: Any, rc: Any) -> list[str]:
        from .models import RealityCheckStatus
        actions = []
        if score is None:
            return ["RUN_MORE_TRADES"]

        if rc and rc.status == RealityCheckStatus.LIKELY_OVERFIT:
            actions.append("REVIEW_OVERFIT")
            actions.append("REQUIRE_WALK_FORWARD")

        if risk and risk.ruin_probability_pct is not None and risk.ruin_probability_pct > 25.0:
            actions.append("REDUCE_CONFIDENCE")
            actions.append("RUN_COST_STRESS")

        if not actions:
            actions.append("NO_ACTION")

        return actions

    def _create_insufficient_data_result(self, request: MonteCarloRequest, start_time: float, warnings: list[str]) -> MonteCarloResult:
        from .models import MonteCarloStatus
        return MonteCarloResult(
            monte_carlo_id=str(uuid.uuid4()),
            request=request,
            status=MonteCarloStatus.INSUFFICIENT_DATA,
            elapsed_seconds=time.time() - start_time,
            paths=[],
            metrics=[],
            distributions=[],
            warnings=warnings + ["Insufficient data to run simulation."]
        )

    def _create_error_result(self, request: MonteCarloRequest, start_time: float, errors: list[str]) -> MonteCarloResult:
        from .models import MonteCarloStatus
        return MonteCarloResult(
            monte_carlo_id=str(uuid.uuid4()),
            request=request,
            status=MonteCarloStatus.ERROR,
            elapsed_seconds=time.time() - start_time,
            paths=[],
            metrics=[],
            distributions=[],
            errors=errors
        )
