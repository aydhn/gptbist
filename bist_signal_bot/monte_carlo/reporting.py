from typing import Any

from .models import (
    MonteCarloResult, MonteCarloRiskSummary, RealityCheckResult,
    MonteCarloMetric, MonteCarloDistribution, MonteCarloPath
)

def monte_carlo_path_to_dict(path: MonteCarloPath) -> dict[str, Any]:
    return {
        "path_id": path.path_id,
        "simulation_index": path.simulation_index,
        "trades_count": path.trades_count,
        "final_equity": path.final_equity,
        "total_return_pct": path.total_return_pct,
        "max_drawdown_pct": path.max_drawdown_pct,
        "ruin_hit": path.ruin_hit
    }

def monte_carlo_metric_to_dict(metric: MonteCarloMetric) -> dict[str, Any]:
    return {
        "metric_id": metric.metric_id,
        "metric_type": metric.metric_type.value,
        "name": metric.name,
        "status": metric.status.value,
        "mean": metric.mean,
        "median": metric.median,
        "std": metric.std,
        "p05": metric.p05,
        "p25": metric.p25,
        "p75": metric.p75,
        "p95": metric.p95,
        "min_value": metric.min_value,
        "max_value": metric.max_value,
        "observed_value": metric.observed_value
    }

def distribution_to_dict(distribution: MonteCarloDistribution) -> dict[str, Any]:
    return {
        "distribution_id": distribution.distribution_id,
        "metric_type": distribution.metric_type.value,
        "percentiles": distribution.percentiles,
        "observations_count": distribution.observations_count,
        "observed_value": distribution.observed_value
    }

def risk_summary_to_dict(summary: MonteCarloRiskSummary) -> dict[str, Any]:
    return {
        "summary_id": summary.summary_id,
        "ruin_probability_pct": summary.ruin_probability_pct,
        "probability_negative_return_pct": summary.probability_negative_return_pct,
        "probability_drawdown_above_threshold_pct": summary.probability_drawdown_above_threshold_pct,
        "expected_tail_loss_pct": summary.expected_tail_loss_pct,
        "cvar_5_pct": summary.cvar_5_pct,
        "median_final_equity": summary.median_final_equity,
        "p05_final_equity": summary.p05_final_equity,
        "p95_final_equity": summary.p95_final_equity
    }

def reality_check_to_dict(result: RealityCheckResult) -> dict[str, Any]:
    return {
        "reality_check_id": result.reality_check_id,
        "status": result.status.value,
        "observed_metric": result.observed_metric,
        "trials_count": result.trials_count,
        "strategy_name": result.strategy_name,
        "symbol": result.symbol,
        "observed_value": result.observed_value,
        "simulated_p_value": result.simulated_p_value,
        "percentile_rank": result.percentile_rank,
        "multiple_testing_warning": result.multiple_testing_warning,
        "disclaimer": result.disclaimer
    }

def monte_carlo_result_to_dict(result: MonteCarloResult) -> dict[str, Any]:
    return {
        "monte_carlo_id": result.monte_carlo_id,
        "request": {
            "request_id": result.request.request_id,
            "target": result.request.target.value,
            "method": result.request.method.value,
            "simulations": result.request.simulations,
            "seed": result.request.seed,
            "initial_equity": result.request.initial_equity,
            "ruin_threshold_pct": result.request.ruin_threshold_pct,
            "strategy_name": result.request.strategy_name,
            "symbol": result.request.symbol,
            "include_cost_randomization": result.request.include_cost_randomization,
            "include_slippage_randomization": result.request.include_slippage_randomization
        },
        "status": result.status.value,
        "generated_at": result.generated_at.isoformat(),
        "elapsed_seconds": result.elapsed_seconds,
        "metrics": [monte_carlo_metric_to_dict(m) for m in result.metrics],
        "distributions": [distribution_to_dict(d) for d in result.distributions],
        "risk_summary": risk_summary_to_dict(result.risk_summary) if result.risk_summary else None,
        "reality_check": reality_check_to_dict(result.reality_check) if result.reality_check else None,
        "robustness_score": result.robustness_score,
        "recommended_actions": result.recommended_actions,
        "warnings": result.warnings,
        "errors": result.errors,
        "disclaimer": result.disclaimer
    }

def paths_to_dataframe(paths: list[MonteCarloPath]) -> Any:
    try:
        import pandas as pd
        data = [monte_carlo_path_to_dict(p) for p in paths]
        return pd.DataFrame(data)
    except ImportError:
        return [monte_carlo_path_to_dict(p) for p in paths]

def metrics_to_dataframe(metrics: list[MonteCarloMetric]) -> Any:
    try:
        import pandas as pd
        data = [monte_carlo_metric_to_dict(m) for m in metrics]
        return pd.DataFrame(data)
    except ImportError:
        return [monte_carlo_metric_to_dict(m) for m in metrics]

def format_monte_carlo_result_text(result: MonteCarloResult) -> str:
    lines = [
        f"Monte Carlo Result (ID: {result.monte_carlo_id})",
        f"Status: {result.status.value}",
        f"Strategy: {result.request.strategy_name or 'N/A'}, Symbol: {result.request.symbol or 'N/A'}",
        f"Simulations: {result.request.simulations}, Method: {result.request.method.value}",
        f"Robustness Score: {result.robustness_score if result.robustness_score is not None else 'N/A'}",
        ""
    ]
    if result.risk_summary:
        lines.append(format_risk_summary_text(result.risk_summary))
    if result.reality_check:
        lines.append(format_reality_check_text(result.reality_check))
    lines.extend([
        "",
        "Recommendations:",
        *[f"- {a}" for a in result.recommended_actions],
        "",
        f"Disclaimer: {result.disclaimer}"
    ])
    return "\n".join(lines)

def format_risk_summary_text(summary: MonteCarloRiskSummary) -> str:
    lines = [
        "Risk Summary:",
        f"- Ruin Probability: {summary.ruin_probability_pct:.2f}%" if summary.ruin_probability_pct is not None else "- Ruin Probability: N/A",
        f"- CVaR (5%): {summary.cvar_5_pct:.2f}%" if summary.cvar_5_pct is not None else "- CVaR (5%): N/A",
        f"- Median Final Equity: {summary.median_final_equity:.2f}" if summary.median_final_equity is not None else "- Median Final Equity: N/A"
    ]
    return "\n".join(lines)

def format_reality_check_text(result: RealityCheckResult) -> str:
    lines = [
        "Reality Check:",
        f"- Status: {result.status.value}",
        f"- p-value: {result.simulated_p_value:.4f}" if result.simulated_p_value is not None else "- p-value: N/A",
        f"- Percentile Rank: {result.percentile_rank:.2f}%" if result.percentile_rank is not None else "- Percentile Rank: N/A"
    ]
    if result.multiple_testing_warning:
        lines.append("- WARNING: Multiple testing bias detected.")
    return "\n".join(lines)

def format_monte_carlo_report_markdown(result: MonteCarloResult) -> str:
    md = [
        f"# Monte Carlo Robustness Report",
        f"**ID:** {result.monte_carlo_id}",
        f"**Generated At:** {result.generated_at.isoformat()}",
        f"**Strategy:** {result.request.strategy_name or 'N/A'}",
        f"**Symbol:** {result.request.symbol or 'N/A'}",
        "",
        "## Configuration",
        f"- Simulations: {result.request.simulations}",
        f"- Method: {result.request.method.value}",
        f"- Seed: {result.request.seed}",
        f"- Cost Randomization: {result.request.include_cost_randomization}",
        "",
        "## Summary",
        f"- **Status:** {result.status.value}",
        f"- **Robustness Score:** {result.robustness_score if result.robustness_score is not None else 'N/A'}",
        ""
    ]

    if result.risk_summary:
        md.extend([
            "## Risk Metrics",
            f"- Ruin Probability: {result.risk_summary.ruin_probability_pct:.2f}%" if result.risk_summary.ruin_probability_pct is not None else "- Ruin Probability: N/A",
            f"- P(Negative Return): {result.risk_summary.probability_negative_return_pct:.2f}%" if result.risk_summary.probability_negative_return_pct is not None else "- P(Negative Return): N/A",
            f"- Median Final Equity: {result.risk_summary.median_final_equity:.2f}" if result.risk_summary.median_final_equity is not None else "- Median Final Equity: N/A",
            ""
        ])

    if result.reality_check:
        md.extend([
            "## Reality Check",
            f"- Status: {result.reality_check.status.value}",
            f"- p-value: {result.reality_check.simulated_p_value:.4f}" if result.reality_check.simulated_p_value is not None else "- p-value: N/A",
            ""
        ])

    if result.warnings:
        md.extend(["## Warnings"])
        md.extend([f"- {w}" for w in result.warnings])
        md.append("")

    md.extend([
        "---",
        f"*{result.disclaimer}*"
    ])

    return "\n".join(md)
