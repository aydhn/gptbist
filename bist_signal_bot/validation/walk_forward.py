import logging
from datetime import datetime
from typing import Any

import pandas as pd

from bist_signal_bot.backtesting.comparison import BenchmarkComparator
from bist_signal_bot.backtesting.engine import BacktestEngine
from bist_signal_bot.backtesting.performance import BacktestPerformanceAnalyzer
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import WalkForwardError
from bist_signal_bot.validation.models import (
    OverfitRiskLevel,
    SplitBacktestResult,
    ValidationConfig,
    ValidationMode,
    WalkForwardResult,
)
from bist_signal_bot.validation.overfit import OverfitRiskAnalyzer
from bist_signal_bot.validation.splits import TimeSeriesSplitGenerator


class WalkForwardAnalyzer:
    def __init__(
        self,
        backtest_engine: BacktestEngine,
        performance_analyzer: BacktestPerformanceAnalyzer | None = None,
        benchmark_comparator: BenchmarkComparator | None = None,
        settings: Settings | None = None,
        logger: logging.Logger | None = None,
    ):
        self.backtest_engine = backtest_engine
        self.performance_analyzer = performance_analyzer or BacktestPerformanceAnalyzer(
            settings=settings
        )
        self.benchmark_comparator = benchmark_comparator or BenchmarkComparator()
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)
        self.overfit_analyzer = OverfitRiskAnalyzer()

    def run_train_test(
        self,
        strategy_name: str,
        symbol: str,
        data: pd.DataFrame,
        params: dict[str, Any] | None = None,
        config: ValidationConfig | None = None,
    ) -> WalkForwardResult:
        config = config or self.build_default_config(mode=ValidationMode.TRAIN_TEST_SPLIT)
        started_at = datetime.now()

        try:
            split = TimeSeriesSplitGenerator.train_test_split(
                data=data,
                train_ratio=config.train_ratio,
                min_train_rows=config.min_train_rows,
                min_test_rows=config.min_test_rows,
                gap_rows=config.gap_rows,
            )
        except Exception as e:
            raise WalkForwardError(f"Failed to generate train/test split: {e}") from e

        train_data, test_data = TimeSeriesSplitGenerator.slice_split_data(data, split)

        train_result = self.backtest_engine.run_single_symbol(
            strategy_name=strategy_name, symbol=symbol, data=train_data, params=params
        )
        train_report = self.performance_analyzer.analyze(train_result)

        test_result = self.backtest_engine.run_single_symbol(
            strategy_name=strategy_name, symbol=symbol, data=test_data, params=params
        )
        test_report = self.performance_analyzer.analyze(test_result)

        benchmark_comparison = None
        if config.compare_benchmark and config.benchmark_name and self.benchmark_comparator:
            try:
                benchmark_result = self.backtest_engine.run_single_symbol(
                    strategy_name=config.benchmark_name, symbol=symbol, data=test_data
                )
                benchmark_report = self.performance_analyzer.analyze(benchmark_result)
                benchmark_comparison = self.benchmark_comparator.compare(
                    test_report, benchmark_report
                )
            except Exception as e:
                self.logger.warning(f"Benchmark comparison failed: {e}")

        split_result = SplitBacktestResult(
            split=split,
            test_result=test_result,
            test_report=test_report,
            train_result=train_result,
            train_report=train_report,
            benchmark_comparison=benchmark_comparison,
            metadata={"mode": "TRAIN_TEST"},
        )

        finished_at = datetime.now()
        elapsed_seconds = (finished_at - started_at).total_seconds()

        aggregate_report = self.aggregate_split_reports([split_result])

        result = WalkForwardResult(
            strategy_name=strategy_name,
            symbol=symbol,
            config=config,
            splits=[split],
            split_results=[split_result],
            aggregate_report=aggregate_report,
            overfit_risk_level=OverfitRiskLevel.UNKNOWN,
            overfit_warnings=[],
            started_at=started_at,
            finished_at=finished_at,
            elapsed_seconds=elapsed_seconds,
        )

        risk_level, warnings = self.overfit_analyzer.assess_walk_forward(result)
        result.overfit_risk_level = risk_level
        result.overfit_warnings = warnings

        return result

    def run_walk_forward(
        self,
        strategy_name: str,
        symbol: str,
        data: pd.DataFrame,
        params: dict[str, Any] | None = None,
        config: ValidationConfig | None = None,
    ) -> WalkForwardResult:
        config = config or self.build_default_config(mode=ValidationMode.WALK_FORWARD)
        started_at = datetime.now()

        try:
            splits = TimeSeriesSplitGenerator.walk_forward_splits(
                data=data,
                train_window_rows=config.train_window_rows or 252,
                test_window_rows=config.test_window_rows,
                step_rows=config.step_rows,
                gap_rows=config.gap_rows,
                expanding=config.expanding,
                max_splits=config.max_splits,
            )
        except Exception as e:
            raise WalkForwardError(f"Failed to generate walk-forward splits: {e}") from e

        split_results = []
        for split in splits:
            train_data, test_data = TimeSeriesSplitGenerator.slice_split_data(data, split)

            train_result = self.backtest_engine.run_single_symbol(
                strategy_name=strategy_name, symbol=symbol, data=train_data, params=params
            )
            train_report = self.performance_analyzer.analyze(train_result)

            test_result = self.backtest_engine.run_single_symbol(
                strategy_name=strategy_name, symbol=symbol, data=test_data, params=params
            )
            test_report = self.performance_analyzer.analyze(test_result)

            split_results.append(
                SplitBacktestResult(
                    split=split,
                    test_result=test_result,
                    test_report=test_report,
                    train_result=train_result,
                    train_report=train_report,
                    metadata={"mode": "WALK_FORWARD"},
                )
            )

        finished_at = datetime.now()
        elapsed_seconds = (finished_at - started_at).total_seconds()

        aggregate_report = self.aggregate_split_reports(split_results)

        result = WalkForwardResult(
            strategy_name=strategy_name,
            symbol=symbol,
            config=config,
            splits=splits,
            split_results=split_results,
            aggregate_report=aggregate_report,
            overfit_risk_level=OverfitRiskLevel.UNKNOWN,
            overfit_warnings=[],
            started_at=started_at,
            finished_at=finished_at,
            elapsed_seconds=elapsed_seconds,
        )

        risk_level, warnings = self.overfit_analyzer.assess_walk_forward(result)
        result.overfit_risk_level = risk_level
        result.overfit_warnings = warnings

        return result

    def aggregate_split_reports(self, split_results: list[SplitBacktestResult]) -> dict[str, Any]:
        if not split_results:
            return {}

        test_returns = [r.test_report.return_metrics.total_return_pct or 0.0 for r in split_results]
        test_sharpes = [
            r.test_report.risk_adjusted_metrics.sharpe_ratio or 0.0 for r in split_results
        ]
        test_dds = [r.test_report.risk_metrics.max_drawdown_pct or 0.0 for r in split_results]
        test_trades = sum(r.test_report.trade_metrics.trade_count or 0 for r in split_results)
        test_win_rates = [
            r.test_report.trade_metrics.win_rate_pct or 0.0
            for r in split_results
            if (r.test_report.trade_metrics.trade_count or 0) > 0
        ]

        mean_win_rate = sum(test_win_rates) / len(test_win_rates) if test_win_rates else 0.0

        sorted_returns = sorted(test_returns)
        n = len(sorted_returns)
        if n % 2 == 0:
            median_return = (sorted_returns[n // 2 - 1] + sorted_returns[n // 2]) / 2.0
        else:
            median_return = sorted_returns[n // 2]

        positive_splits = sum(1 for r in test_returns if r > 0)
        positive_split_pct = (positive_splits / n) * 100 if n > 0 else 0.0

        stability_score = 0.0
        if test_returns:
            mean_ret = sum(test_returns) / len(test_returns)
            variance = sum((x - mean_ret) ** 2 for x in test_returns) / len(test_returns)
            stability_score = min(100.0, max(0.0, positive_split_pct - (variance**0.5)))

        return {
            "split_count": n,
            "mean_test_return_pct": sum(test_returns) / n,
            "median_test_return_pct": median_return,
            "min_test_return_pct": min(test_returns),
            "max_test_return_pct": max(test_returns),
            "mean_test_sharpe": sum(test_sharpes) / n,
            "mean_test_max_drawdown_pct": sum(test_dds) / n,
            "positive_test_split_pct": positive_split_pct,
            "total_test_trades": test_trades,
            "mean_win_rate_pct": mean_win_rate,
            "stability_score": stability_score,
        }

    def build_default_config(
        self, mode: ValidationMode = ValidationMode.WALK_FORWARD
    ) -> ValidationConfig:
        return ValidationConfig(
            mode=mode,
            train_ratio=getattr(self.settings, "VALIDATION_TRAIN_RATIO", 0.7),
            min_train_rows=getattr(self.settings, "VALIDATION_MIN_TRAIN_ROWS", 150),
            min_test_rows=getattr(self.settings, "VALIDATION_MIN_TEST_ROWS", 50),
            train_window_rows=getattr(self.settings, "VALIDATION_TRAIN_WINDOW_ROWS", 252),
            test_window_rows=getattr(self.settings, "VALIDATION_TEST_WINDOW_ROWS", 63),
            step_rows=getattr(self.settings, "VALIDATION_STEP_ROWS", 63),
            gap_rows=getattr(self.settings, "VALIDATION_GAP_ROWS", 0),
            expanding=getattr(self.settings, "VALIDATION_EXPANDING", False),
            max_splits=getattr(self.settings, "VALIDATION_MAX_SPLITS", 10),
            compare_benchmark=getattr(self.settings, "VALIDATION_COMPARE_BENCHMARK", False),
            benchmark_name=getattr(self.settings, "VALIDATION_BENCHMARK_NAME", "buy_and_hold"),
            save_reports=getattr(self.settings, "VALIDATION_SAVE_REPORTS", False),
        )
