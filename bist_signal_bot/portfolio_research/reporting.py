import pandas as pd
from typing import Any
from bist_signal_bot.portfolio_research.models import (
    ResearchPortfolioItem,
    ResearchPortfolioSnapshot,
    RebalancePlan,
    BasketSimulationResult,
    PortfolioConstraint,
    PortfolioExposureBucket,
    CorrelationPair
)

def portfolio_item_to_dict(item: ResearchPortfolioItem) -> dict[str, Any]:
    return item.model_dump()

def snapshot_to_dict(snapshot: ResearchPortfolioSnapshot) -> dict[str, Any]:
    d = snapshot.model_dump()
    if "created_at" in d and hasattr(d["created_at"], "isoformat"):
        d["created_at"] = d["created_at"].isoformat()
    return d

def rebalance_plan_to_dict(plan: RebalancePlan) -> dict[str, Any]:
    d = plan.model_dump()
    if "created_at" in d and hasattr(d["created_at"], "isoformat"):
        d["created_at"] = d["created_at"].isoformat()
    return d

def basket_simulation_to_dict(result: BasketSimulationResult) -> dict[str, Any]:
    d = result.model_dump()
    if "created_at" in d and hasattr(d["created_at"], "isoformat"):
        d["created_at"] = d["created_at"].isoformat()
    if "start_date" in d and hasattr(d["start_date"], "isoformat"):
        d["start_date"] = d["start_date"].isoformat()
    if "end_date" in d and hasattr(d["end_date"], "isoformat"):
        d["end_date"] = d["end_date"].isoformat()
    return d

def items_to_dataframe(items: list[ResearchPortfolioItem]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame()
    return pd.DataFrame([item.model_dump() for item in items])

def exposures_to_dataframe(exposures: list[PortfolioExposureBucket]) -> pd.DataFrame:
    if not exposures:
        return pd.DataFrame()
    return pd.DataFrame([b.model_dump() for b in exposures])

def constraints_to_dataframe(constraints: list[PortfolioConstraint]) -> pd.DataFrame:
    if not constraints:
        return pd.DataFrame()
    return pd.DataFrame([c.model_dump() for c in constraints])

def correlations_to_dataframe(pairs: list[CorrelationPair]) -> pd.DataFrame:
    if not pairs:
        return pd.DataFrame()
    return pd.DataFrame([p.model_dump() for p in pairs])

def format_snapshot_text(snapshot: ResearchPortfolioSnapshot) -> str:
    lines = [
        f"Research Portfolio Snapshot: {snapshot.snapshot_id}",
        f"Created At: {snapshot.created_at}",
        f"Mode: {snapshot.mode.value}",
        f"Method: {snapshot.allocation_method.value}",
        f"Total Weight: {snapshot.total_weight:.2%}",
        f"Items: {snapshot.item_count} ({snapshot.valid_item_count} valid)",
        "",
        "ITEMS:"
    ]
    for i in snapshot.items:
        lines.append(f"  {i.symbol}: {i.final_weight:.2%} (Proposed: {i.proposed_weight:.2%}, State: {i.state})")

    lines.append("")
    lines.append(snapshot.disclaimer)
    return "\n".join(lines)

def format_rebalance_plan_text(plan: RebalancePlan) -> str:
    lines = [
        f"Rebalance Plan: {plan.plan_id}",
        f"Target Snapshot: {plan.target_snapshot_id}",
        f"Turnover Estimate: {plan.turnover_estimate:.2%}",
        "",
        "DELTAS:"
    ]
    for i in plan.items:
        lines.append(f"  {i.symbol}: {i.current_weight:.2%} -> {i.target_weight:.2%} (Delta: {i.delta_weight:+.2%}) [{i.decision.value}]")

    lines.append("")
    lines.append(plan.disclaimer)
    return "\n".join(lines)

def format_basket_simulation_text(result: BasketSimulationResult) -> str:
    lines = [
        f"Basket Simulation: {result.simulation_id}",
        f"Date Range: {result.start_date.strftime('%Y-%m-%d')} to {result.end_date.strftime('%Y-%m-%d')}",
        f"Simulated Return: {result.simulated_return_pct:.2f}%",
    ]
    if result.max_drawdown_pct is not None:
        lines.append(f"Max Drawdown: {result.max_drawdown_pct:.2f}%")
    if result.volatility_pct is not None:
        lines.append(f"Volatility: {result.volatility_pct:.2f}%")

    lines.append("")
    lines.append(result.disclaimer)
    return "\n".join(lines)

def format_portfolio_report_markdown(snapshot: ResearchPortfolioSnapshot) -> str:
    md = [
        f"# Research Portfolio Report",
        f"**Snapshot ID:** `{snapshot.snapshot_id}`",
        f"**Created At:** {snapshot.created_at}",
        f"**Allocation Method:** {snapshot.allocation_method.value}",
        f"**Total Weight:** {snapshot.total_weight:.2%}",
        "",
        "## Disclaimer",
        f"> {snapshot.disclaimer}",
        "",
        "## Allocations",
        "| Symbol | Final Weight | State | Score | Warnings |",
        "|--------|-------------|-------|-------|----------|"
    ]

    for i in snapshot.items:
        w_str = f"{i.final_weight:.2%}"
        s_str = f"{i.score:.1f}" if i.score else "-"
        warns = ", ".join(i.warnings) if i.warnings else "-"
        state = i.state or "-"
        md.append(f"| {i.symbol} | {w_str} | {state} | {s_str} | {warns} |")

    md.extend(["", "## Exposures", "| Group | Key | Weight | Items |", "|-------|-----|--------|-------|"])
    for e in snapshot.exposures:
        if e.weight > 0:
            md.append(f"| {e.group.value} | {e.key} | {e.weight:.2%} | {e.item_count} |")

    return "\n".join(md)
