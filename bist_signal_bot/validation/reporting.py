import csv
import json
from datetime import datetime
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.validation.models import RobustnessResult, WalkForwardResult


class ValidationReportWriter:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def _get_output_dir(self, output_dir: Path | None = None) -> Path:
        if output_dir:
            path = Path(output_dir)
        else:
            from bist_signal_bot.storage.paths import get_validation_reports_dir

            path = get_validation_reports_dir(self.settings)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _generate_filename_prefix(self, prefix: str, strategy: str, symbol: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{strategy}_{symbol}_{timestamp}"

    def save_walk_forward_json(
        self, result: WalkForwardResult, output_dir: Path | None = None
    ) -> Path:
        dir_path = self._get_output_dir(output_dir)
        prefix = self._generate_filename_prefix("wf", result.strategy_name, result.symbol)
        file_path = dir_path / f"{prefix}.json"

        data = result.summary()
        data["split_results"] = [sr.summary() for sr in result.split_results]
        data["started_at"] = result.started_at.isoformat()
        data["finished_at"] = result.finished_at.isoformat()
        data["elapsed_seconds"] = result.elapsed_seconds

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return file_path

    def save_walk_forward_markdown(
        self, result: WalkForwardResult, output_dir: Path | None = None
    ) -> Path:
        dir_path = self._get_output_dir(output_dir)
        prefix = self._generate_filename_prefix("wf", result.strategy_name, result.symbol)
        file_path = dir_path / f"{prefix}.md"

        content = self.format_walk_forward_markdown(result)

        with open(file_path, "w") as f:
            f.write(content)

        return file_path

    def save_walk_forward_csv(
        self, result: WalkForwardResult, output_dir: Path | None = None
    ) -> dict[str, Path]:
        dir_path = self._get_output_dir(output_dir)
        prefix = self._generate_filename_prefix("wf", result.strategy_name, result.symbol)

        paths = {}

        summary_path = dir_path / f"{prefix}_split_summary.csv"
        with open(summary_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "split_id",
                    "test_return_pct",
                    "test_sharpe",
                    "test_max_drawdown",
                    "test_trades",
                    "train_return_pct",
                ]
            )
            for sr in result.split_results:
                train_ret = (
                    sr.train_report.return_metrics.total_return_pct if sr.train_report else ""
                )
                writer.writerow(
                    [
                        sr.split.split_id,
                        f"{sr.test_report.return_metrics.total_return_pct or 0.0:.2f}",
                        f"{sr.test_report.risk_adjusted_metrics.sharpe_ratio or 0.0:.2f}",
                        f"{sr.test_report.risk_metrics.max_drawdown_pct or 0.0:.2f}",
                        sr.test_report.trade_metrics.trade_count or 0,
                        f"{train_ret:.2f}" if isinstance(train_ret, float) else train_ret,
                    ]
                )
        paths["split_summary"] = summary_path

        return paths

    def save_robustness_json(
        self, result: RobustnessResult, output_dir: Path | None = None
    ) -> Path:
        dir_path = self._get_output_dir(output_dir)
        prefix = self._generate_filename_prefix("rob", result.strategy_name, result.symbol)
        file_path = dir_path / f"{prefix}.json"

        data = result.summary()
        data["generated_at"] = result.generated_at.isoformat()
        data["elapsed_seconds"] = result.elapsed_seconds

        run_data = []
        for r in result.run_results:
            run_data.append(
                {
                    "params": r.params,
                    "return_pct": r.performance_report.return_metrics.total_return_pct,
                    "sharpe": r.performance_report.risk_adjusted_metrics.sharpe_ratio,
                    "max_drawdown": r.performance_report.risk_metrics.max_drawdown_pct,
                }
            )
        data["runs"] = run_data

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return file_path

    def save_robustness_markdown(
        self, result: RobustnessResult, output_dir: Path | None = None
    ) -> Path:
        dir_path = self._get_output_dir(output_dir)
        prefix = self._generate_filename_prefix("rob", result.strategy_name, result.symbol)
        file_path = dir_path / f"{prefix}.md"

        content = self.format_robustness_markdown(result)

        with open(file_path, "w") as f:
            f.write(content)

        return file_path

    def save_robustness_csv(self, result: RobustnessResult, output_dir: Path | None = None) -> Path:
        dir_path = self._get_output_dir(output_dir)
        prefix = self._generate_filename_prefix("rob", result.strategy_name, result.symbol)
        file_path = dir_path / f"{prefix}.csv"

        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            if result.run_results:
                param_keys = list(result.run_results[0].params.keys())
                header = [*param_keys, "return_pct", "sharpe", "max_drawdown_pct", "trades"]
                writer.writerow(header)

                for r in result.run_results:
                    row = [r.params.get(k, "") for k in param_keys]
                    row.extend(
                        [
                            f"{r.performance_report.return_metrics.total_return_pct or 0.0:.2f}",
                            f"{r.performance_report.risk_adjusted_metrics.sharpe_ratio or 0.0:.2f}",
                            f"{r.performance_report.risk_metrics.max_drawdown_pct or 0.0:.2f}",
                            r.performance_report.trade_metrics.trade_count or 0,
                        ]
                    )
                    writer.writerow(row)

        return file_path

    def format_walk_forward_markdown(self, result: WalkForwardResult) -> str:
        lines = [
            "# Walk-Forward Analysis Report",
            f"**Generated At:** {result.finished_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Strategy:** {result.strategy_name}",
            f"**Symbol:** {result.symbol}",
            f"**Mode:** {result.config.mode.value}",
            "",
            "## Disclaimer",
            f"*{result.disclaimer}*",
            "",
            "## Aggregate OOS Metrics",
            f"- **Splits Analyzed:** {result.aggregate_report.get('split_count', 0)}",
            f"- **Mean OOS Return:** {result.aggregate_report.get('mean_test_return_pct', 0):.2f}%",
            f"- **Positive Split %:** {result.aggregate_report.get('positive_test_split_pct', 0):.2f}%",  # noqa: E501
            f"- **Mean Max Drawdown:** {result.aggregate_report.get('mean_test_max_drawdown_pct', 0):.2f}%",  # noqa: E501
            f"- **Stability Score:** {result.aggregate_report.get('stability_score', 0):.2f}",
            f"- **Overfit Risk Level:** {result.overfit_risk_level.value}",
            "",
            "## Overfit Warnings",
        ]

        if result.overfit_warnings:
            for w in result.overfit_warnings:
                lines.append(f"- {w}")
        else:
            lines.append("- No immediate overfit warnings.")

        lines.append("")
        lines.append("## Split Summary")
        lines.append("| Split ID | Test Return % | Train Return % | Test Sharpe | Test Max DD % |")
        lines.append("|---|---|---|---|---|")

        for sr in result.split_results:
            train_ret = (
                f"{sr.train_report.return_metrics.total_return_pct:.2f}"
                if sr.train_report
                else "N/A"
            )
            lines.append(
                f"| {sr.split.split_id} "
                f"| {sr.test_report.return_metrics.total_return_pct or 0.0:.2f} "
                f"| {train_ret} "
                f"| {sr.test_report.risk_adjusted_metrics.sharpe_ratio or 0.0:.2f} "
                f"| {sr.test_report.risk_metrics.max_drawdown_pct or 0.0:.2f} |"
            )

        lines.append("")
        lines.append("## Limitations")
        lines.append(
            "- This report assumes historical market conditions. Future performance is not guaranteed."  # noqa: E501
        )
        lines.append(
            "- Simulation limits apply. Slippage and commission models are approximations."
        )

        return "\n".join(lines)

    def format_robustness_markdown(self, result: RobustnessResult) -> str:
        lines = [
            "# Parameter Robustness Report",
            f"**Generated At:** {result.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Strategy:** {result.strategy_name}",
            f"**Symbol:** {result.symbol}",
            "",
            "## Disclaimer",
            f"*{result.disclaimer}*",
            "",
            "## Summary",
            f"- **Total Runs:** {len(result.run_results)}",
            f"- **Stability Score:** {result.stability_score:.2f} / 100",
            f"- **Overfit Risk Level:** {result.overfit_risk_level.value}",
            "",
            "## Best Parameters",
            "```json",
            json.dumps(result.best_params, indent=2, default=str),
            "```",
            "",
            "## Worst Parameters",
            "```json",
            json.dumps(result.worst_params, indent=2, default=str),
            "```",
            "",
            "## Warnings",
        ]

        if result.warnings:
            for w in result.warnings:
                lines.append(f"- {w}")
        else:
            lines.append("- No robustness warnings detected.")

        return "\n".join(lines)
