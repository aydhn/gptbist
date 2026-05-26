import pandas as pd
from typing import Any

from bist_signal_bot.portfolio_ledger.models import (
    ResearchPortfolio,
    ResearchPortfolioPosition,
    PortfolioLedgerEvent,
    PortfolioValuationSnapshot,
    PortfolioAttributionItem,
    PortfolioAttributionResult,
    PortfolioOutcomeResult,
    RebalanceTrackingResult,
    PortfolioNavPoint,
    PortfolioLedgerReport
)

def portfolio_position_to_dict(position: ResearchPortfolioPosition) -> dict[str, Any]:
    return position.model_dump()

def research_portfolio_to_dict(portfolio: ResearchPortfolio) -> dict[str, Any]:
    return portfolio.model_dump()

def portfolio_event_to_dict(event: PortfolioLedgerEvent) -> dict[str, Any]:
    return event.model_dump()

def valuation_snapshot_to_dict(snapshot: PortfolioValuationSnapshot) -> dict[str, Any]:
    return snapshot.model_dump()

def attribution_item_to_dict(item: PortfolioAttributionItem) -> dict[str, Any]:
    return item.model_dump()

def attribution_result_to_dict(result: PortfolioAttributionResult) -> dict[str, Any]:
    return result.model_dump()

def portfolio_outcome_to_dict(result: PortfolioOutcomeResult) -> dict[str, Any]:
    return result.model_dump()

def rebalance_tracking_to_dict(result: RebalanceTrackingResult) -> dict[str, Any]:
    return result.model_dump()

def nav_point_to_dict(point: PortfolioNavPoint) -> dict[str, Any]:
    return point.model_dump()

def portfolio_ledger_report_to_dict(report: PortfolioLedgerReport) -> dict[str, Any]:
    return report.model_dump()

def positions_to_dataframe(positions: list[ResearchPortfolioPosition]) -> pd.DataFrame:
    data = [p.model_dump() for p in positions]
    return pd.DataFrame(data)

def nav_points_to_dataframe(points: list[PortfolioNavPoint]) -> pd.DataFrame:
    data = [p.model_dump() for p in points]
    if data:
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        return df
    return pd.DataFrame()

def attribution_to_dataframe(items: list[PortfolioAttributionItem]) -> pd.DataFrame:
    data = [i.model_dump() for i in items]
    return pd.DataFrame(data)

def format_research_portfolio_text(portfolio: ResearchPortfolio) -> str:
    lines = [
        f"Research Portfolio: {portfolio.name} ({portfolio.portfolio_id})",
        f"Status: {portfolio.status.value}",
        f"Initial Notional: {portfolio.initial_notional} {portfolio.base_currency}",
        f"Positions: {len(portfolio.positions)}"
    ]
    if portfolio.current_simulated_nav is not None:
        lines.append(f"Simulated NAV: {portfolio.current_simulated_nav:.2f} {portfolio.base_currency}")
    lines.append("")
    lines.append(portfolio.disclaimer)
    return "\n".join(lines)

def format_valuation_snapshot_text(snapshot: PortfolioValuationSnapshot) -> str:
    lines = [
        f"Valuation Snapshot: {snapshot.valuation_id}",
        f"Generated At: {snapshot.generated_at}",
        f"Simulated NAV: {snapshot.simulated_nav:.2f}",
        f"Gross Return: {snapshot.gross_return_pct:.2f}%" if snapshot.gross_return_pct is not None else "Gross Return: N/A",
        f"Net Return: {snapshot.net_return_pct:.2f}%" if snapshot.net_return_pct is not None else "Net Return: N/A",
        f"Total Cost Drag: {snapshot.total_cost_drag_pct:.2f}%" if snapshot.total_cost_drag_pct is not None else "Total Cost Drag: N/A",
        f"Status: {snapshot.status.value}"
    ]
    if snapshot.missing_prices:
        lines.append(f"Missing Prices: {', '.join(snapshot.missing_prices)}")
    lines.append("")
    lines.append(snapshot.disclaimer)
    return "\n".join(lines)

def format_attribution_result_text(result: PortfolioAttributionResult) -> str:
    lines = [
        f"Portfolio Attribution",
        f"Total Gross Return: {result.total_gross_return_pct:.2f}%" if result.total_gross_return_pct is not None else "Total Gross Return: N/A",
        f"Top Positive Contributors: {', '.join(result.top_positive_contributors)}",
        f"Top Negative Contributors: {', '.join(result.top_negative_contributors)}"
    ]
    lines.append("")
    lines.append(result.disclaimer)
    return "\n".join(lines)

def format_portfolio_outcome_text(result: PortfolioOutcomeResult) -> str:
    lines = [
        f"Portfolio Outcome (Horizon: {result.horizon_days} days)",
        f"Label: {result.label.value}",
        f"Net Return: {result.net_return_pct:.2f}%" if result.net_return_pct is not None else "Net Return: N/A",
        f"Benchmark Excess: {result.excess_return_pct:.2f}%" if result.excess_return_pct is not None else "Benchmark Excess: N/A"
    ]
    lines.append("")
    lines.append(result.disclaimer)
    return "\n".join(lines)

def format_rebalance_tracking_text(result: RebalanceTrackingResult) -> str:
    lines = [
        f"Rebalance Tracking",
        f"Quality Delta: {result.quality_delta:.2f}" if result.quality_delta is not None else "Quality Delta: N/A",
        f"Estimated Turnover: {result.estimated_turnover_pct:.2f}%" if result.estimated_turnover_pct is not None else "Estimated Turnover: N/A",
        f"Violations Before: {result.violations_before} -> After: {result.violations_after}"
    ]
    lines.append("")
    lines.append(result.disclaimer)
    return "\n".join(lines)

def format_portfolio_ledger_report_markdown(report: PortfolioLedgerReport) -> str:
    lines = [
        f"# Portfolio Ledger Report",
        f"Generated At: {report.generated_at}",
        ""
    ]

    if report.key_findings:
        lines.append("## Key Findings")
        for k in report.key_findings:
            lines.append(f"- {k}")
        lines.append("")

    lines.append(f"> {report.disclaimer}")

    return "\n".join(lines)
