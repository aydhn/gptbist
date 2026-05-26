import pandas as pd
from typing import Any
from bist_signal_bot.whatif.models import (
    WhatIfRunResult, WhatIfScenarioResult, WhatIfComparisonResult,
    CapitalScalingResult, PolicySandboxResult, SensitivityFinding,
    WhatIfAssumptionOverride, WhatIfScenario
)

def assumption_override_to_dict(override: WhatIfAssumptionOverride) -> dict[str, Any]:
    return override.model_dump()

def scenario_to_dict(scenario: WhatIfScenario) -> dict[str, Any]:
    return scenario.model_dump()

def scenario_result_to_dict(result: WhatIfScenarioResult) -> dict[str, Any]:
    return result.model_dump()

def sensitivity_finding_to_dict(finding: SensitivityFinding) -> dict[str, Any]:
    return finding.model_dump()

def comparison_to_dict(result: WhatIfComparisonResult) -> dict[str, Any]:
    return result.model_dump()

def capital_scaling_to_dict(result: CapitalScalingResult) -> dict[str, Any]:
    return result.model_dump()

def policy_sandbox_to_dict(result: PolicySandboxResult) -> dict[str, Any]:
    return result.model_dump()

def whatif_run_to_dict(result: WhatIfRunResult) -> dict[str, Any]:
    return result.safe_public_dict()

def scenario_results_to_dataframe(results: list[WhatIfScenarioResult]) -> pd.DataFrame:
    data = []
    for r in results:
        data.append({
            "scenario_name": r.scenario.name,
            "status": r.status.value,
            "portfolio_score": r.portfolio_score,
            "diversification_score": r.diversification_score,
            "net_quality_score": r.estimated_net_quality_score,
            "total_cost_bps": r.estimated_total_cost_bps,
            "turnover_pct": r.estimated_turnover_pct,
            "expected_signal_count": r.expected_signal_count,
            "violations": r.constraint_violations_count
        })
    return pd.DataFrame(data)

def sensitivity_to_dataframe(findings: list[SensitivityFinding]) -> pd.DataFrame:
    data = []
    for f in findings:
        data.append({
            "assumption_type": f.assumption_type.value,
            "metric_name": f.metric_name,
            "delta_pct": f.delta_pct,
            "direction": f.direction.value,
            "severity": f.severity
        })
    return pd.DataFrame(data)

def format_scenario_result_text(result: WhatIfScenarioResult) -> str:
    lines = [
        f"Scenario: {result.scenario.name} ({result.status.value})",
        f"Net Quality Score: {result.estimated_net_quality_score}",
        f"Total Cost (bps): {result.estimated_total_cost_bps}",
        f"Turnover (%): {result.estimated_turnover_pct}",
        f"Constraint Violations: {result.constraint_violations_count}",
        "",
        result.scenario.disclaimer
    ]
    return "\n".join(lines)

def format_comparison_text(result: WhatIfComparisonResult) -> str:
    lines = [
        "What-If Comparison Result",
        "=" * 25,
        f"Best Scenario ID: {result.best_scenario_id}",
        f"Worst Scenario ID: {result.worst_scenario_id}",
        "",
        "Key Findings:"
    ]
    for kf in result.key_findings:
        lines.append(f"- {kf}")
    lines.extend(["", result.disclaimer])
    return "\n".join(lines)

def format_capital_scaling_text(result: CapitalScalingResult) -> str:
    lines = [
        "Capital Scaling Result",
        "=" * 22,
        f"Best Research Notional: {result.best_research_notional}",
        "",
        "Capacity Warnings:"
    ]
    for cw in result.capacity_warnings:
        lines.append(f"- {cw}")
    lines.extend(["", result.disclaimer])
    return "\n".join(lines)

def format_policy_sandbox_text(result: PolicySandboxResult) -> str:
    lines = [
        "Policy Sandbox Result",
        "=" * 21,
        f"Policy Name: {result.policy_name}",
        f"Selected Candidate: {result.selected_policy_candidate.get('name') if result.selected_policy_candidate else 'None'}",
        "",
        result.disclaimer
    ]
    return "\n".join(lines)

def format_whatif_report_markdown(result: WhatIfRunResult) -> str:
    lines = [
        f"# What-If Scenario Lab Report",
        f"**Run ID:** {result.run_id}",
        f"**Source Type:** {result.request.source_type}",
        f"**Generated At:** {result.generated_at}",
        f"**Status:** {result.status.value}",
        "",
        "## Scenarios Overview"
    ]

    for r in result.scenario_results:
        lines.append(f"- **{r.scenario.name}**: Net Quality {r.estimated_net_quality_score}, Cost {r.estimated_total_cost_bps} bps")

    if result.comparison:
        lines.extend([
            "",
            "## Comparison Key Findings",
            *[f"- {kf}" for kf in result.comparison.key_findings]
        ])

    if result.capital_scaling:
        lines.extend([
            "",
            "## Capital Scaling Warnings",
            *[f"- {w}" for w in result.capital_scaling.capacity_warnings]
        ])

    lines.extend([
        "",
        "---",
        f"*{result.disclaimer}*"
    ])

    return "\n".join(lines)
