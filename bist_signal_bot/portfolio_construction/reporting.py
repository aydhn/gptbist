from typing import Any, Dict, List
import pandas as pd

from bist_signal_bot.portfolio_construction.models import (
    PortfolioCandidate, PortfolioPositionResearch, PortfolioConstraint,
    PortfolioConstraintViolation, CorrelationCluster, RiskBudgetItem,
    PortfolioConstructionResult, RebalanceSimulation
)

def candidate_to_dict(candidate: PortfolioCandidate) -> Dict[str, Any]:
    return candidate.model_dump()

def position_to_dict(position: PortfolioPositionResearch) -> Dict[str, Any]:
    return position.model_dump()

def constraint_to_dict(constraint: PortfolioConstraint) -> Dict[str, Any]:
    return constraint.model_dump()

def violation_to_dict(violation: PortfolioConstraintViolation) -> Dict[str, Any]:
    return violation.model_dump()

def cluster_to_dict(cluster: CorrelationCluster) -> Dict[str, Any]:
    return cluster.model_dump()

def risk_budget_item_to_dict(item: RiskBudgetItem) -> Dict[str, Any]:
    return item.model_dump()

def construction_result_to_dict(result: PortfolioConstructionResult) -> Dict[str, Any]:
    import json
    return json.loads(result.model_dump_json())

def rebalance_to_dict(simulation: RebalanceSimulation) -> Dict[str, Any]:
    import json
    return json.loads(simulation.model_dump_json())

def positions_to_dataframe(positions: List[PortfolioPositionResearch]) -> pd.DataFrame:
    if not positions:
        return pd.DataFrame()
    return pd.DataFrame([p.model_dump() for p in positions])

def candidates_to_dataframe(candidates: List[PortfolioCandidate]) -> pd.DataFrame:
    if not candidates:
        return pd.DataFrame()
    return pd.DataFrame([c.model_dump() for c in candidates])

def format_portfolio_construction_text(result: PortfolioConstructionResult) -> str:
    lines = [
        "BIST Bot Portfolio Construction Result",
        "=" * 40,
        f"Result ID: {result.result_id}",
        f"Generated At: {result.generated_at.isoformat()}",
        f"Status: {result.status.value}",
        f"Weighting Method: {result.weighting_method.value}",
        f"Diversification Score: {result.diversification_score or 'N/A'}",
        f"Portfolio Score: {result.portfolio_score or 'N/A'}",
        f"Estimated Turnover: {result.estimated_turnover_pct or 0.0}%",
        f"Constraint Violations: {len(result.violations)}",
        "",
        "Positions:",
    ]
    for p in result.positions:
        lines.append(f"  {p.symbol}: {p.target_weight:.2%}")

    lines.extend([
        "",
        "Disclaimer:",
        result.disclaimer
    ])
    return "\n".join(lines)

def format_rebalance_simulation_text(simulation: RebalanceSimulation) -> str:
    lines = [
        "BIST Bot Rebalance Simulation",
        "=" * 30,
        f"Rebalance ID: {simulation.rebalance_id}",
        f"Turnover: {simulation.estimated_turnover_pct:.2f}%",
        f"Estimated Cost: {simulation.estimated_cost_bps or 0.0} bps",
        "",
        "Actions:"
    ]
    for action in simulation.actions:
        lines.append(f"  {action['symbol']}: {action['action']} (Target: {action['target_weight']:.2%})")

    lines.extend([
        "",
        "Disclaimer:",
        simulation.disclaimer
    ])
    return "\n".join(lines)

def format_constraints_text(violations: List[PortfolioConstraintViolation]) -> str:
    if not violations:
        return "No constraint violations."

    lines = ["Portfolio Constraint Violations", "=" * 30]
    for v in violations:
        lines.append(f"[{v.severity.value}] {v.message} (Action: {v.recommended_action})")
    return "\n".join(lines)

def format_risk_budget_text(items: List[RiskBudgetItem]) -> str:
    if not items:
        return "No risk budget items."

    lines = ["Risk Budget Contribution", "=" * 30]
    for item in items:
        lines.append(f"{item.symbol}: Vol {item.volatility_pct or 0.0:.2f}%, CTR {item.contribution_to_risk_pct or 0.0:.2f}%")
    return "\n".join(lines)

def format_portfolio_construction_report_markdown(result: PortfolioConstructionResult) -> str:
    md = [
        f"# Portfolio Construction Report",
        f"**Date**: {result.generated_at.isoformat()}",
        f"**Status**: {result.status.value}",
        f"**Method**: {result.weighting_method.value}",
        "",
        "## Summary",
        f"- **Diversification Score**: {result.diversification_score or 'N/A'}",
        f"- **Portfolio Score**: {result.portfolio_score or 'N/A'}",
        f"- **Estimated Turnover**: {result.estimated_turnover_pct or 0.0}%",
        f"- **Estimated Cost**: {result.estimated_total_cost_bps or 0.0} bps",
        "",
        "## Positions"
    ]
    for p in result.positions:
        md.append(f"- **{p.symbol}**: {p.target_weight:.2%} (Score: {p.candidate_score or 'N/A'})")

    if result.violations:
        md.append("\n## Constraint Violations")
        for v in result.violations:
            md.append(f"- **[{v.severity.value}]**: {v.message}")

    md.extend([
        "",
        "---",
        f"*{result.disclaimer}*"
    ])

    return "\n".join(md)
