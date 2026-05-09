import pandas as pd
from typing import Any

from bist_signal_bot.optimization.models import (
    OptimizationResult, WalkForwardOptimizationResult, OptimizationTrial
)

def optimization_result_to_dict(result: OptimizationResult) -> dict[str, Any]:
    return {
        "summary": result.summary(),
        "config": result.config.model_dump() if hasattr(result.config, "model_dump") else result.config.dict(),
        "search_spaces": [s.model_dump() if hasattr(s, "model_dump") else s.dict() for s in result.search_spaces],
        "top_trials": [t.summary() for t in result.top_trials],
        "warnings": result.warnings,
        "disclaimer": result.disclaimer
    }

def walk_forward_optimization_to_dict(result: WalkForwardOptimizationResult) -> dict[str, Any]:
    return {
        "summary": result.summary(),
        "config": result.config.model_dump() if hasattr(result.config, "model_dump") else result.config.dict(),
        "split_results": [
            {
                "split_id": sr.split_id,
                "train_start": sr.train_start.isoformat(),
                "train_end": sr.train_end.isoformat(),
                "test_start": sr.test_start.isoformat(),
                "test_end": sr.test_end.isoformat(),
                "train_best_params": sr.train_best_trial.params if sr.train_best_trial else None,
                "test_score": sr.test_trial.objective_score if sr.test_trial else None
            } for sr in result.split_results
        ],
        "warnings": result.overfit_warnings,
        "disclaimer": result.disclaimer
    }

def trials_to_dataframe(trials: list[OptimizationTrial]) -> pd.DataFrame:
    data = []
    for t in trials:
        row = {"trial_id": t.trial_id, "status": t.status.value, "passed": t.constraint_passed, "score": t.objective_score}
        row.update(t.params)

        if t.performance_report:
             row["total_return"] = t.performance_report.return_metrics.total_return_pct
             row["sharpe"] = t.performance_report.risk_adjusted_metrics.sharpe_ratio
             row["max_dd"] = t.performance_report.risk_metrics.max_drawdown_pct
             row["trades"] = t.performance_report.trade_metrics.trade_count

        data.append(row)

    return pd.DataFrame(data)

def top_trials_to_dataframe(result: OptimizationResult) -> pd.DataFrame:
    return trials_to_dataframe(result.top_trials)

def format_optimization_markdown(result: OptimizationResult) -> str:
    lines = [
        f"# Optimization Report: {result.strategy_name} on {result.symbol}",
        "",
        f"**Method:** {result.method.value}  ",
        f"**Objective:** {result.objective.value}  ",
        f"**Started At:** {result.started_at.isoformat()}  ",
        f"**Elapsed:** {result.elapsed_seconds:.2f}s  ",
        f"**Status:** {result.status.value}  ",
        "",
        "## Search Space",
    ]

    for s in result.search_spaces:
         if s.values:
             lines.append(f"- **{s.name}**: {s.values}")
         elif s.min_value is not None:
             lines.append(f"- **{s.name}**: [{s.min_value} to {s.max_value} step {s.step}]")
         elif s.choices:
             lines.append(f"- **{s.name}**: {s.choices}")

    lines.extend([
        "",
        "## Results Summary",
        f"- Total combinations planned: {result.total_combinations_planned}",
        f"- Total trials run: {result.total_trials_run}",
        f"- Failed trials: {result.failed_trials}",
        ""
    ])

    if result.best_trial:
         lines.extend([
             "## Best Parameters",
             "```json",
             str(result.best_trial.params),
             "```",
             f"- Score: {result.best_trial.objective_score:.2f}",
             f"- Passed constraints: {result.best_trial.constraint_passed}"
         ])

    if result.warnings:
         lines.extend(["", "## Warnings"])
         for w in result.warnings:
              lines.append(f"- {w}")

    lines.extend([
         "",
         "## Disclaimer",
         f"_{result.disclaimer}_"
    ])

    return "\n".join(lines)

def format_walk_forward_optimization_markdown(result: WalkForwardOptimizationResult) -> str:
    lines = [
        f"# Walk-Forward Optimization Report: {result.strategy_name} on {result.symbol}",
        "",
        f"**Method:** {result.config.method.value}  ",
        f"**Objective:** {result.config.objective.value}  ",
        f"**Splits:** {len(result.split_results)}  ",
        f"**Status:** {result.status.value}  ",
        "",
        "## Aggregate Results",
        f"- Stability Score: {result.parameter_stability_score:.2f}%",
        f"- Mean OOS Return: {result.mean_oos_return_pct:.2f}%" if result.mean_oos_return_pct is not None else "- Mean OOS Return: N/A",
        f"- Mean OOS Sharpe: {result.mean_oos_sharpe:.2f}" if result.mean_oos_sharpe is not None else "- Mean OOS Sharpe: N/A",
        f"- Positive OOS Splits: {result.positive_oos_split_pct:.1f}%" if result.positive_oos_split_pct is not None else "- Positive OOS Splits: N/A",
        ""
    ]

    lines.append("## Split Details")
    for sr in result.split_results:
         lines.append(f"### Split {sr.split_id}")
         lines.append(f"- Train: {sr.train_start.date()} to {sr.train_end.date()}")
         lines.append(f"- Test: {sr.test_start.date()} to {sr.test_end.date()}")
         if sr.train_best_trial:
             lines.append(f"- Best Train Params: {sr.train_best_trial.params}")
             lines.append(f"- Train Score: {sr.train_best_trial.objective_score:.2f}" if sr.train_best_trial.objective_score else "- Train Score: N/A")
         if sr.test_trial:
             lines.append(f"- OOS Score: {sr.test_trial.objective_score:.2f}" if sr.test_trial.objective_score else "- OOS Score: N/A")
         lines.append("")

    if result.overfit_warnings:
         lines.extend(["## Overfit Warnings"])
         for w in result.overfit_warnings:
              lines.append(f"- {w}")

    lines.extend([
         "",
         "## Disclaimer",
         f"_{result.disclaimer}_"
    ])

    return "\n".join(lines)

def format_optimization_text(result: OptimizationResult | WalkForwardOptimizationResult) -> str:
    # A simplified text version suitable for CLI output
    if isinstance(result, OptimizationResult):
         summary = result.summary()
         lines = [
              f"Optimization Complete: {summary['strategy']} on {summary['symbol']}",
              f"Method: {summary['method']} | Objective: {summary['objective']}",
              f"Status: {summary['status']} | Run: {summary['total_trials_run']}",
              f"Best Score: {summary['best_score']:.2f}" if summary['best_score'] is not None else "Best Score: N/A",
              f"Best Params: {summary['best_params']}"
         ]
         if result.warnings:
              lines.append(f"Warnings: {len(result.warnings)}")

    else:
         summary = result.summary()
         lines = [
              f"WF Optimization Complete: {summary['strategy']} on {summary['symbol']}",
              f"Method: {result.config.method.value} | Splits: {summary['splits']}",
              f"Status: {summary['status']} | Stability: {summary['parameter_stability_score']:.1f}%",
              f"Mean OOS Return: {summary['mean_oos_return_pct']:.2f}%" if summary['mean_oos_return_pct'] is not None else "Mean OOS Return: N/A",
              f"Positive OOS Pct: {summary['positive_oos_split_pct']:.1f}%" if summary['positive_oos_split_pct'] is not None else "Positive OOS Pct: N/A"
         ]
         if result.overfit_warnings:
              lines.append(f"Overfit Warnings: {len(result.overfit_warnings)}")

    return "\n".join(lines)
