import pandas as pd
from typing import Any

from bist_signal_bot.stress.models import (
    StressTestResult,
    MonteCarloResult,
    ShockScenarioResult,
    DrawdownSimulationResult,
    RiskOfRuinResult
)

def stress_result_to_dict(result: StressTestResult) -> dict[str, Any]:
    return result.model_dump()

def monte_carlo_to_dict(result: MonteCarloResult) -> dict[str, Any]:
    return result.model_dump()

def shock_result_to_dict(result: ShockScenarioResult) -> dict[str, Any]:
    return result.model_dump()

def drawdown_result_to_dict(result: DrawdownSimulationResult) -> dict[str, Any]:
    return result.model_dump()

def risk_of_ruin_to_dict(result: RiskOfRuinResult) -> dict[str, Any]:
    return result.model_dump()

def shock_results_to_dataframe(results: list[ShockScenarioResult]) -> pd.DataFrame:
    data = []
    for r in results:
        data.append({
            "Scenario": r.scenario.name,
            "Severity": r.scenario.severity.value,
            "Portfolio Impact %": round(r.estimated_portfolio_impact_pct, 2) if r.estimated_portfolio_impact_pct is not None else None,
            "Status": r.status.value
        })
    return pd.DataFrame(data)

def format_stress_result_text(result: StressTestResult) -> str:
    lines = [
        "=== STRESS TEST RESULT ===",
        f"Rating: {result.stress_rating.value}",
        f"Score: {result.stress_score:.2f}" if result.stress_score else "Score: N/A",
        f"Status: {result.status.value}",
        f"Warnings: {len(result.warnings)}"
    ]
    if result.monte_carlo_result:
        p05 = result.monte_carlo_result.final_return_pct_p05
        lines.append(f"MC p05 Return: {p05:.2f}%" if p05 is not None else "MC p05 Return: N/A")

    if result.risk_of_ruin_result:
        prob = result.risk_of_ruin_result.estimated_ruin_probability_pct
        lines.append(f"Risk of Ruin: {prob:.2f}%" if prob is not None else "Risk of Ruin: N/A")

    lines.append("")
    lines.append("Note: " + result.disclaimer)
    return "\n".join(lines)

def format_monte_carlo_text(result: MonteCarloResult) -> str:
    lines = [
        "=== MONTE CARLO ===",
        f"Simulations: {result.config.simulations}",
        f"Horizon: {result.config.horizon_days} days",
        f"Status: {result.status.value}"
    ]
    if result.final_return_pct_p50 is not None:
        lines.append(f"Median Return: {result.final_return_pct_p50:.2f}%")
    if result.max_drawdown_pct_p50 is not None:
        lines.append(f"Median Max Drawdown: {result.max_drawdown_pct_p50:.2f}%")
    lines.append("")
    lines.append("Note: " + result.disclaimer)
    return "\n".join(lines)

def format_shock_result_text(result: ShockScenarioResult) -> str:
    lines = [
        f"=== SHOCK: {result.scenario.name} ===",
        f"Severity: {result.scenario.severity.value}",
        f"Status: {result.status.value}"
    ]
    impact = result.estimated_portfolio_impact_pct
    lines.append(f"Est. Impact: {impact:.2f}%" if impact is not None else "Est. Impact: N/A")
    lines.append("")
    lines.append("Note: " + result.disclaimer)
    return "\n".join(lines)

def format_stress_report_markdown(result: StressTestResult) -> str:
    md = [
        "# Stress Test Research Report",
        "",
        f"**ID:** `{result.stress_id}`",
        f"**Status:** {result.status.value}",
        f"**Rating:** {result.stress_rating.value}",
        f"**Warnings:** {len(result.warnings)}",
        "",
        "## Disclaimer",
        f"*{result.disclaimer}*",
        ""
    ]

    if result.monte_carlo_result:
        md.append("## Monte Carlo Simulation")
        mc = result.monte_carlo_result
        md.append(f"- **Simulations:** {mc.config.simulations}")
        md.append(f"- **Method:** {mc.config.method.value}")
        md.append(f"- **5th Percentile Return:** {mc.final_return_pct_p05:.2f}%" if mc.final_return_pct_p05 is not None else "- **5th Percentile Return:** N/A")
        md.append(f"- **Median Return:** {mc.final_return_pct_p50:.2f}%" if mc.final_return_pct_p50 is not None else "- **Median Return:** N/A")
        md.append("")

    if result.shock_results:
        md.append("## Shock Scenarios")
        df = shock_results_to_dataframe(result.shock_results)
        md.append(df.to_markdown(index=False))
        md.append("")

    if result.drawdown_result:
        md.append("## Drawdown Simulation")
        dd = result.drawdown_result
        md.append(f"- **Max Drawdown:** {dd.max_drawdown_pct:.2f}%" if dd.max_drawdown_pct is not None else "- **Max Drawdown:** N/A")
        md.append(f"- **Longest Duration:** {dd.longest_drawdown_days} days" if dd.longest_drawdown_days is not None else "- **Longest Duration:** N/A")
        md.append("")

    if result.risk_of_ruin_result:
        md.append("## Risk of Ruin Estimate")
        rr = result.risk_of_ruin_result
        md.append(f"- **Threshold:** {rr.ruin_threshold_pct:.2f}%")
        md.append(f"- **Probability:** {rr.estimated_ruin_probability_pct:.2f}%" if rr.estimated_ruin_probability_pct is not None else "- **Probability:** N/A")
        md.append(f"- **Worst Streak:** {rr.worst_loss_streak} days" if rr.worst_loss_streak is not None else "- **Worst Streak:** N/A")
        md.append("")

    return "\n".join(md)
