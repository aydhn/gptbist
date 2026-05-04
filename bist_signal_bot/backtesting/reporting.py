import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_backtest_results_dir
from bist_signal_bot.backtesting.models import (
    BacktestResult,
    BenchmarkComparisonReport,
    BacktestReportBundle
)
from bist_signal_bot.backtesting.performance import BacktestPerformanceAnalyzer
from bist_signal_bot.backtesting.drawdown import calculate_drawdown_curve
from bist_signal_bot.backtesting.reports import build_trades_dataframe
from bist_signal_bot.core.exceptions import BacktestReportError

class BacktestReportWriter:
    def __init__(self, settings: Optional[Settings] = None, base_dir: Optional[Path] = None, logger: Optional[logging.Logger] = None):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)
        self.base_dir = base_dir or get_backtest_results_dir(self.settings)
        self.performance_analyzer = BacktestPerformanceAnalyzer(self.settings)

    def build_report_bundle(
        self,
        result: BacktestResult,
        benchmark_comparisons: Optional[list[BenchmarkComparisonReport]] = None
    ) -> BacktestReportBundle:
        try:
            perf_report = self.performance_analyzer.analyze(result)
            trades_df = build_trades_dataframe(result.trades)

            drawdown_df = pd.DataFrame()
            if not result.equity_curve.empty:
                drawdown_df = calculate_drawdown_curve(result.equity_curve)

            return BacktestReportBundle(
                backtest_result=result,
                performance_report=perf_report,
                benchmark_comparisons=benchmark_comparisons or [],
                equity_curve=result.equity_curve,
                drawdown_curve=drawdown_df,
                trades=trades_df,
                generated_at=datetime.now(timezone.utc),
                output_files={},
                metadata={}
            )
        except Exception as e:
            raise BacktestReportError(f"Failed to build report bundle: {str(e)}")

    def _get_filename_prefix(self, bundle: BacktestReportBundle) -> str:
        ts = bundle.generated_at.strftime("%Y%m%d_%H%M%S")
        sym = bundle.performance_report.symbol or "PORTFOLIO"
        strat = bundle.performance_report.strategy_name
        return f"{ts}_{strat}_{sym}"

    def save_json(self, bundle: BacktestReportBundle, output_dir: Optional[Path] = None) -> Path:
        out_dir = output_dir or self.base_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        prefix = self._get_filename_prefix(bundle)
        file_path = out_dir / f"{prefix}_report.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(bundle.summary(), f, indent=2)

        bundle.output_files["json"] = str(file_path)
        return file_path

    def save_markdown(self, bundle: BacktestReportBundle, output_dir: Optional[Path] = None) -> Path:
        out_dir = output_dir or self.base_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        prefix = self._get_filename_prefix(bundle)
        file_path = out_dir / f"{prefix}_report.md"

        content = self.format_markdown_report(bundle)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        bundle.output_files["markdown"] = str(file_path)
        return file_path

    def save_csv_files(self, bundle: BacktestReportBundle, output_dir: Optional[Path] = None) -> dict[str, Path]:
        out_dir = output_dir or self.base_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        prefix = self._get_filename_prefix(bundle)

        files = {}

        if not bundle.equity_curve.empty:
            p = out_dir / f"{prefix}_equity_curve.csv"
            bundle.equity_curve.to_csv(p)
            files["equity_curve"] = p
            bundle.output_files["equity_curve_csv"] = str(p)

        if not bundle.drawdown_curve.empty:
            p = out_dir / f"{prefix}_drawdown_curve.csv"
            bundle.drawdown_curve.to_csv(p)
            files["drawdown_curve"] = p
            bundle.output_files["drawdown_curve_csv"] = str(p)

        if not bundle.trades.empty:
            p = out_dir / f"{prefix}_trades.csv"
            bundle.trades.to_csv(p, index=False)
            files["trades"] = p
            bundle.output_files["trades_csv"] = str(p)

        return files

    def save_bundle(
        self,
        bundle: BacktestReportBundle,
        formats: Optional[list[str]] = None,
        output_dir: Optional[Path] = None
    ) -> dict[str, Path]:
        if not formats:
            formats_str = self.settings.BACKTEST_REPORT_FORMATS
            formats = [f.strip().lower() for f in formats_str.split(",")]
            if "all" in formats:
                formats = ["json", "markdown", "csv"]

        paths = {}
        if "json" in formats:
            paths["json"] = self.save_json(bundle, output_dir)
        if "markdown" in formats:
            paths["markdown"] = self.save_markdown(bundle, output_dir)
        if "csv" in formats:
            csv_paths = self.save_csv_files(bundle, output_dir)
            paths.update({f"csv_{k}": v for k, v in csv_paths.items()})

        return paths

    def format_markdown_report(self, bundle: BacktestReportBundle) -> str:
        pr = bundle.performance_report

        md = [
            f"# Backtest Report: {pr.strategy_name} ({pr.symbol})",
            "",
            "## Disclaimer",
            f"> {pr.disclaimer}",
            "",
            "## Summary",
            f"- **Initial Capital:** {pr.initial_capital:.2f}",
            f"- **Final Equity:** {pr.final_equity:.2f}",
            f"- **Total Return:** {pr.return_metrics.total_return_pct:.2f}%",
            f"- **Annualized Return:** {pr.return_metrics.annualized_return_pct:.2f}%" if pr.return_metrics.annualized_return_pct else "- **Annualized Return:** N/A",
            f"- **Max Drawdown:** {pr.risk_metrics.max_drawdown_pct:.2f}%" if pr.risk_metrics.max_drawdown_pct is not None else "- **Max Drawdown:** N/A",
            f"- **Sharpe Ratio:** {pr.risk_adjusted_metrics.sharpe_ratio:.2f}" if pr.risk_adjusted_metrics.sharpe_ratio is not None else "- **Sharpe Ratio:** N/A",
            "",
            "## Trade Metrics",
            f"- **Total Trades:** {pr.trade_metrics.trade_count}",
            f"- **Win Rate:** {pr.trade_metrics.win_rate_pct:.2f}%" if pr.trade_metrics.win_rate_pct is not None else "- **Win Rate:** N/A",
            f"- **Profit Factor:** {pr.trade_metrics.profit_factor:.2f}" if pr.trade_metrics.profit_factor is not None else "- **Profit Factor:** N/A",
            "",
            "## Cost Metrics",
            f"- **Total Cost:** {pr.cost_metrics.total_cost:.2f}"
        ]

        if bundle.benchmark_comparisons:
            md.extend(["", "## Benchmark Comparisons"])
            for comp in bundle.benchmark_comparisons:
                out_str = "Yes" if comp.outperform else "No"
                md.extend([
                    f"### vs {comp.benchmark_name}",
                    f"- **Strategy Return:** {comp.strategy_total_return_pct:.2f}%",
                    f"- **Benchmark Return:** {comp.benchmark_total_return_pct:.2f}%",
                    f"- **Excess Return:** {comp.excess_return_pct:.2f}%",
                    f"- **Outperform:** {out_str}"
                ])

        if pr.warnings:
            md.extend(["", "## Warnings"])
            for w in pr.warnings:
                md.append(f"- {w}")

        return "\n".join(md)
