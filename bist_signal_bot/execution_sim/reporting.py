from typing import Any
import pandas as pd

from bist_signal_bot.execution_sim.models import (
    TransactionCostBreakdown, SlippageEstimate, LiquiditySnapshot,
    SimulatedOrder, SimulatedFill, ExecutionQualityReport
)

def cost_breakdown_to_dict(breakdown: TransactionCostBreakdown) -> dict[str, Any]:
    return breakdown.model_dump()

def slippage_estimate_to_dict(estimate: SlippageEstimate) -> dict[str, Any]:
    return estimate.model_dump()

def liquidity_snapshot_to_dict(snapshot: LiquiditySnapshot) -> dict[str, Any]:
    return snapshot.model_dump()

def simulated_order_to_dict(order: SimulatedOrder) -> dict[str, Any]:
    return order.model_dump()

def simulated_fill_to_dict(fill: SimulatedFill) -> dict[str, Any]:
    return fill.model_dump()

def quality_report_to_dict(report: ExecutionQualityReport) -> dict[str, Any]:
    return report.model_dump()

def fills_to_dataframe(fills: list[SimulatedFill]) -> pd.DataFrame:
    data = [f.model_dump() for f in fills]
    return pd.DataFrame(data)

def liquidity_to_dataframe(snapshots: list[LiquiditySnapshot]) -> pd.DataFrame:
    data = [s.model_dump() for s in snapshots]
    return pd.DataFrame(data)

def format_cost_breakdown_text(breakdown: TransactionCostBreakdown) -> str:
    return (
        f"Cost Breakdown for {breakdown.side.value} Notional: {breakdown.notional:.2f}\n"
        f"Total Cost: {breakdown.total_cost:.2f} (BPS: {breakdown.total_cost_bps})\n"
        f"Net Notional: {breakdown.net_notional:.2f}\n"
        f"Disclaimer: {breakdown.disclaimer}"
    )

def format_slippage_estimate_text(estimate: SlippageEstimate) -> str:
    return (
        f"Slippage Estimate for {estimate.symbol} {estimate.side.value}:\n"
        f"Ref Price: {estimate.reference_price:.2f} -> Fill Price: {estimate.estimated_fill_price:.2f} ({estimate.estimated_slippage_bps} bps)\n"
        f"Disclaimer: {estimate.disclaimer}"
    )

def format_liquidity_snapshot_text(snapshot: LiquiditySnapshot) -> str:
    return (
        f"Liquidity for {snapshot.symbol}: {snapshot.status.value}\n"
        f"Avg Turnover: {snapshot.average_turnover}"
    )

def format_simulated_fill_text(fill: SimulatedFill) -> str:
    return (
        f"Simulated Fill: {fill.symbol} {fill.status.value} (Filled: {fill.filled_quantity})\n"
        f"Gross: {fill.gross_notional:.2f}, Net: {fill.net_notional:.2f}\n"
        f"Disclaimer: {fill.disclaimer}"
    )

def format_execution_quality_text(report: ExecutionQualityReport) -> str:
    return (
        f"Execution Quality: {report.symbol} - Fill Rate: {report.fill_rate_pct}% ({report.filled_orders}/{report.total_orders})\n"
        f"Avg Slippage (bps): {report.average_slippage_bps}\n"
        f"Disclaimer: {report.disclaimer}"
    )

def format_execution_report_markdown(report: ExecutionQualityReport) -> str:
    return (
        f"# Execution Quality Report\n"
        f"**Symbol**: {report.symbol}\n"
        f"**Fill Rate**: {report.fill_rate_pct}%\n"
        f"**Disclaimer**: {report.disclaimer}\n"
    )
