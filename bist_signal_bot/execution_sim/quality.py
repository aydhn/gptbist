from typing import Any
import uuid

from bist_signal_bot.execution_sim.models import SimulatedFill, ExecutionQualityReport, SimulatedFillStatus, SimulatedOrderSide

class ExecutionQualityAnalyzer:
    def __init__(self, settings: Any | None = None):
        self.settings = settings

    def analyze_fills(self, fills: list[SimulatedFill], symbol: str | None = None, strategy_name: str | None = None) -> ExecutionQualityReport:
        total = len(fills)
        filled = sum(1 for f in fills if f.status == SimulatedFillStatus.FILLED)
        partial = sum(1 for f in fills if f.status == SimulatedFillStatus.PARTIAL_FILLED)
        not_filled = sum(1 for f in fills if f.status in [SimulatedFillStatus.NOT_FILLED, SimulatedFillStatus.REJECTED_RESEARCH])

        gross_pnl = 0.0
        net_pnl = 0.0
        total_cost = 0.0
        slippage_sum = 0.0
        cost_bps_sum = 0.0
        valid_slips = 0
        valid_costs = 0

        for f in fills:
            if f.cost_breakdown:
                total_cost += f.cost_breakdown.total_cost
                if f.cost_breakdown.total_cost_bps is not None:
                    cost_bps_sum += f.cost_breakdown.total_cost_bps
                    valid_costs += 1
            if f.slippage_estimate and f.slippage_estimate.estimated_slippage_bps is not None:
                slippage_sum += f.slippage_estimate.estimated_slippage_bps
                valid_slips += 1

        # PNL assumes round trip pairs or is just a summation of net notional (simplistic for report)
        # We leave gross_pnl/net_pnl as None unless explicitly calculated later

        avg_slip = (slippage_sum / valid_slips) if valid_slips > 0 else None
        avg_cost_bps = (cost_bps_sum / valid_costs) if valid_costs > 0 else None

        return ExecutionQualityReport(
            report_id=str(uuid.uuid4()),
            symbol=symbol,
            strategy_name=strategy_name,
            fills=fills,
            total_orders=total,
            filled_orders=filled,
            partial_orders=partial,
            not_filled_orders=not_filled,
            gross_pnl=None,
            net_pnl=None,
            total_cost=total_cost,
            average_slippage_bps=avg_slip,
            average_total_cost_bps=avg_cost_bps,
            fill_rate_pct=self.fill_rate(fills)
        )

    def fill_rate(self, fills: list[SimulatedFill]) -> float | None:
        if not fills:
            return None
        return (sum(1 for f in fills if f.status in [SimulatedFillStatus.FILLED, SimulatedFillStatus.PARTIAL_FILLED]) / len(fills)) * 100.0

    def average_slippage_bps(self, fills: list[SimulatedFill]) -> float | None:
        valid = [f.slippage_estimate.estimated_slippage_bps for f in fills if f.slippage_estimate and f.slippage_estimate.estimated_slippage_bps is not None]
        if not valid: return None
        return sum(valid) / len(valid)

    def average_total_cost_bps(self, fills: list[SimulatedFill]) -> float | None:
        valid = [f.cost_breakdown.total_cost_bps for f in fills if f.cost_breakdown and f.cost_breakdown.total_cost_bps is not None]
        if not valid: return None
        return sum(valid) / len(valid)

    def gross_vs_net_pnl(self, trades_or_fills: list[Any]) -> dict[str, Any]:
        # Implementation placeholder for backtest trades integration
        return {"gross_pnl": 0.0, "net_pnl": 0.0, "cost_drag": 0.0}

    def cost_drag_pct(self, gross_return_pct: float | None, net_return_pct: float | None) -> float | None:
        if gross_return_pct is None or net_return_pct is None:
            return None
        return gross_return_pct - net_return_pct
