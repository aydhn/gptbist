import math
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.backtesting.models import BacktestPerformanceReport
from bist_signal_bot.optimization.models import ObjectiveMetric, OptimizationConstraints

class ObjectiveScorer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def score(self, report: BacktestPerformanceReport, objective: ObjectiveMetric, constraints: OptimizationConstraints | None = None, benchmark_excess_return_pct: float | None = None) -> tuple[float, list[str]]:
        if constraints:
            passed, violations = self.check_constraints(report, constraints)
            if not passed:
                return 0.0, violations

        raw_score = 0.0
        if objective == ObjectiveMetric.TOTAL_RETURN:
            raw_score = self.score_total_return(report)
        elif objective == ObjectiveMetric.ANNUALIZED_RETURN:
             ann_ret = report.return_metrics.annualized_return_pct
             raw_score = ann_ret if ann_ret is not None else 0.0
        elif objective == ObjectiveMetric.SHARPE:
            raw_score = self.score_sharpe(report)
        elif objective == ObjectiveMetric.SORTINO:
            raw_score = self.score_sortino(report)
        elif objective == ObjectiveMetric.CALMAR:
            raw_score = self.score_calmar(report)
        elif objective == ObjectiveMetric.PROFIT_FACTOR:
            raw_score = self.score_profit_factor(report)
        elif objective == ObjectiveMetric.MAX_DRAWDOWN:
            dd = report.risk_metrics.max_drawdown_pct
            # Higher score for lower drawdown (closer to 0)
            raw_score = -abs(dd) if dd is not None else -100.0
        elif objective == ObjectiveMetric.WIN_RATE:
            wr = report.trade_metrics.win_rate_pct
            raw_score = wr if wr is not None else 0.0
        elif objective == ObjectiveMetric.EXPECTANCY:
             exp = report.trade_metrics.expectancy
             raw_score = exp if exp is not None else 0.0
        elif objective == ObjectiveMetric.COMPOSITE:
            raw_score = self.score_composite(report, benchmark_excess_return_pct)
        else:
            raw_score = self.score_composite(report, benchmark_excess_return_pct)

        # Sanity check score
        if math.isnan(raw_score) or math.isinf(raw_score):
            raw_score = 0.0

        # Clamp to 0-100 if composite, others are unbounded
        if objective == ObjectiveMetric.COMPOSITE:
            raw_score = max(0.0, min(100.0, raw_score))

        return raw_score, []

    def score_total_return(self, report: BacktestPerformanceReport) -> float:
        return report.return_metrics.total_return_pct or 0.0

    def score_sharpe(self, report: BacktestPerformanceReport) -> float:
        sharpe = report.risk_adjusted_metrics.sharpe_ratio
        return sharpe if sharpe is not None else -10.0

    def score_sortino(self, report: BacktestPerformanceReport) -> float:
        sortino = report.risk_adjusted_metrics.sortino_ratio
        return sortino if sortino is not None else -10.0

    def score_calmar(self, report: BacktestPerformanceReport) -> float:
        calmar = report.risk_adjusted_metrics.calmar_ratio
        return calmar if calmar is not None else -10.0

    def score_profit_factor(self, report: BacktestPerformanceReport) -> float:
        pf = report.trade_metrics.profit_factor
        return pf if pf is not None else 0.0

    def score_composite(self, report: BacktestPerformanceReport, benchmark_excess_return_pct: float | None = None) -> float:
        ret_pct = report.return_metrics.total_return_pct or 0.0
        sharpe = report.risk_adjusted_metrics.sharpe_ratio or 0.0
        sortino = report.risk_adjusted_metrics.sortino_ratio or 0.0
        calmar = report.risk_adjusted_metrics.calmar_ratio or 0.0
        pf = report.trade_metrics.profit_factor or 0.0
        dd_pct = report.risk_metrics.max_drawdown_pct or 0.0

        # Normalize to rough 0-100 scales for components
        # Return: assuming 100% is a great score
        norm_ret = max(0, min(100, ret_pct))

        # Sharpe: 0=0, 2=50, 4=100
        norm_sharpe = max(0, min(100, sharpe * 25))

        # Sortino: 0=0, 3=50, 6=100
        norm_sortino = max(0, min(100, sortino * 16.6))

        # Calmar: 0=0, 1=50, 2=100
        norm_calmar = max(0, min(100, calmar * 50))

        # Profit Factor: 1=0, 2=50, 3=100
        norm_pf = max(0, min(100, (pf - 1) * 50))

        # Drawdown: 0=100, 40=0
        norm_dd = max(0, 100 - (abs(dd_pct) * 2.5))

        w_ret = getattr(self.settings, "OPTIMIZATION_COMPOSITE_RETURN_WEIGHT", 0.25)
        w_sharpe = getattr(self.settings, "OPTIMIZATION_COMPOSITE_SHARPE_WEIGHT", 0.20)
        w_sortino = getattr(self.settings, "OPTIMIZATION_COMPOSITE_SORTINO_WEIGHT", 0.15)
        w_calmar = getattr(self.settings, "OPTIMIZATION_COMPOSITE_CALMAR_WEIGHT", 0.15)
        w_pf = getattr(self.settings, "OPTIMIZATION_COMPOSITE_PROFIT_FACTOR_WEIGHT", 0.10)
        w_dd = getattr(self.settings, "OPTIMIZATION_COMPOSITE_DRAWDOWN_WEIGHT", 0.10)
        w_bench = getattr(self.settings, "OPTIMIZATION_COMPOSITE_BENCHMARK_WEIGHT", 0.05)

        score = (
            (norm_ret * w_ret) +
            (norm_sharpe * w_sharpe) +
            (norm_sortino * w_sortino) +
            (norm_calmar * w_calmar) +
            (norm_pf * w_pf) +
            (norm_dd * w_dd)
        )

        if benchmark_excess_return_pct is not None:
             # Normalize excess return: 0=50, +20=100, -20=0
             norm_bench = max(0, min(100, 50 + (benchmark_excess_return_pct * 2.5)))
             score += norm_bench * w_bench
        else:
             # Distribute benchmark weight to return if missing
             score += norm_ret * w_bench

        # Trade count penalty
        min_trades = getattr(self.settings, "OPTIMIZATION_MIN_TRADES", 3)
        if report.trade_metrics.trade_count < min_trades:
             penalty = (min_trades - report.trade_metrics.trade_count) / min_trades
             score = score * (1 - (penalty * 0.5)) # Up to 50% penalty

        return max(0.0, min(100.0, score))


    def check_constraints(self, report: BacktestPerformanceReport, constraints: OptimizationConstraints) -> tuple[bool, list[str]]:
        violations = []

        if constraints.min_trades > 0 and report.trade_metrics.trade_count < constraints.min_trades:
            violations.append(f"Trade count ({report.trade_metrics.trade_count}) < min_trades ({constraints.min_trades})")

        if constraints.max_drawdown_pct is not None:
            dd = report.risk_metrics.max_drawdown_pct
            if dd is not None and abs(dd) > constraints.max_drawdown_pct:
                violations.append(f"Max drawdown ({abs(dd):.1f}%) > max_drawdown_pct ({constraints.max_drawdown_pct}%)")

        if constraints.min_profit_factor is not None:
            pf = report.trade_metrics.profit_factor
            if pf is None or pf < constraints.min_profit_factor:
                 pf_str = f"{pf:.2f}" if pf is not None else "None"
                 violations.append(f"Profit factor ({pf_str}) < min_profit_factor ({constraints.min_profit_factor})")

        if constraints.min_sharpe is not None:
             sharpe = report.risk_adjusted_metrics.sharpe_ratio
             if sharpe is None or sharpe < constraints.min_sharpe:
                 sharpe_str = f"{sharpe:.2f}" if sharpe is not None else "None"
                 violations.append(f"Sharpe ({sharpe_str}) < min_sharpe ({constraints.min_sharpe})")

        if constraints.min_total_return_pct is not None:
             ret = report.return_metrics.total_return_pct
             if ret is None or ret < constraints.min_total_return_pct:
                 ret_str = f"{ret:.2f}" if ret is not None else "None"
                 violations.append(f"Total return ({ret_str}%) < min_total_return_pct ({constraints.min_total_return_pct}%)")

        if constraints.require_positive_return:
             ret = report.return_metrics.total_return_pct
             if ret is None or ret <= 0:
                  violations.append("Return is not positive")

        if constraints.max_cost_pct_of_profit is not None:
             cost_pct = report.cost_metrics.cost_as_pct_of_gross_profit
             if cost_pct is not None and cost_pct > constraints.max_cost_pct_of_profit:
                 violations.append(f"Cost of profit ({cost_pct:.1f}%) > max_cost_pct ({constraints.max_cost_pct_of_profit}%)")

        return len(violations) == 0, violations
