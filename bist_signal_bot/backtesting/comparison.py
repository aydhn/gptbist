import logging
from datetime import datetime, timezone
from typing import Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.backtesting.models import (
    BacktestResult,
    BacktestPerformanceReport,
    BenchmarkComparisonReport
)
from bist_signal_bot.benchmarks.engine import BenchmarkEngine
from bist_signal_bot.backtesting.performance import BacktestPerformanceAnalyzer

class BenchmarkComparator:
    def __init__(
        self,
        benchmark_engine: Optional[BenchmarkEngine] = None,
        performance_analyzer: Optional[BacktestPerformanceAnalyzer] = None,
        settings: Optional[Settings] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.settings = settings or Settings()
        self.benchmark_engine = benchmark_engine or BenchmarkEngine(settings=self.settings)
        self.performance_analyzer = performance_analyzer or BacktestPerformanceAnalyzer(settings=self.settings)
        self.logger = logger or logging.getLogger(__name__)

    def compare_backtest_to_benchmark(
        self,
        strategy_result: BacktestResult,
        benchmark_result: Optional[BacktestResult] = None,
        benchmark_name: str = "buy_and_hold"
    ) -> BenchmarkComparisonReport:
        strategy_report = self.performance_analyzer.analyze(strategy_result)

        if benchmark_result:
             benchmark_report = self.performance_analyzer.analyze(benchmark_result)
             return self.compare_reports(strategy_report, benchmark_report, benchmark_name)

        return BenchmarkComparisonReport(
            strategy_name=strategy_result.strategy_name,
            benchmark_name=benchmark_name,
            symbol=strategy_result.symbol,
            strategy_total_return_pct=strategy_report.return_metrics.total_return_pct,
            benchmark_total_return_pct=0.0,
            excess_return_pct=strategy_report.return_metrics.total_return_pct,
            strategy_max_drawdown_pct=strategy_report.risk_metrics.max_drawdown_pct,
            benchmark_max_drawdown_pct=None,
            strategy_sharpe=strategy_report.risk_adjusted_metrics.sharpe_ratio,
            benchmark_sharpe=None,
            outperform=None,
            warnings=["No benchmark backtest result provided. Showing strategy metrics only."],
            generated_at=datetime.now(timezone.utc),
            metadata={"comparison_valid": False}
        )

    def compare_reports(
        self,
        strategy_report: BacktestPerformanceReport,
        benchmark_report: BacktestPerformanceReport,
        benchmark_name: str
    ) -> BenchmarkComparisonReport:
        strat_return = strategy_report.return_metrics.total_return_pct
        bench_return = benchmark_report.return_metrics.total_return_pct
        excess = strat_return - bench_return
        outperform = excess > 0

        warnings = []
        if strategy_report.timeframe != benchmark_report.timeframe:
             warnings.append("Timeframes do not match between strategy and benchmark.")
        warnings.append("Benchmark comparison is for historical analysis only. Outperformance does not imply future success.")

        return BenchmarkComparisonReport(
            strategy_name=strategy_report.strategy_name,
            benchmark_name=benchmark_name,
            symbol=strategy_report.symbol,
            strategy_total_return_pct=strat_return,
            benchmark_total_return_pct=bench_return,
            excess_return_pct=excess,
            strategy_max_drawdown_pct=strategy_report.risk_metrics.max_drawdown_pct,
            benchmark_max_drawdown_pct=benchmark_report.risk_metrics.max_drawdown_pct,
            strategy_sharpe=strategy_report.risk_adjusted_metrics.sharpe_ratio,
            benchmark_sharpe=benchmark_report.risk_adjusted_metrics.sharpe_ratio,
            outperform=outperform,
            warnings=warnings,
            generated_at=datetime.now(timezone.utc),
            metadata={
                "strategy_timeframe": strategy_report.timeframe,
                "benchmark_timeframe": benchmark_report.timeframe
            }
        )

    def compare_many(
        self,
        strategy_report: BacktestPerformanceReport,
        benchmark_reports: dict[str, BacktestPerformanceReport]
    ) -> list[BenchmarkComparisonReport]:
        return [
            self.compare_reports(strategy_report, report, name)
            for name, report in benchmark_reports.items()
        ]
