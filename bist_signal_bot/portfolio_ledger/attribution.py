from datetime import datetime, timezone
import uuid
from typing import Any
from collections import defaultdict

from bist_signal_bot.portfolio_ledger.models import (
    PortfolioValuationSnapshot,
    PortfolioAttributionResult,
    PortfolioAttributionItem,
    AttributionType,
    PortfolioValuationStatus
)
from bist_signal_bot.core.exceptions import PortfolioAttributionError

class PortfolioAttributionEngine:
    def __init__(self):
        pass

    def calculate_attribution(self, snapshot: PortfolioValuationSnapshot, by: AttributionType = AttributionType.SYMBOL) -> PortfolioAttributionResult:
        if by == AttributionType.SYMBOL:
            items = self.symbol_attribution(snapshot)
        elif by == AttributionType.SECTOR:
            items = self.sector_attribution(snapshot)
        elif by == AttributionType.STRATEGY:
            items = self.strategy_attribution(snapshot)
        elif by == AttributionType.COST:
            items = self.cost_attribution(snapshot)
        elif by == AttributionType.RISK_BUDGET:
            items = self.risk_budget_attribution(snapshot)
        else:
            raise PortfolioAttributionError(f"Unsupported attribution type: {by}")

        ranked_items = self.rank_contributors(items)

        # Sort for top positive/negative
        sorted_by_gross = sorted([i for i in items if i.gross_contribution_pct is not None],
                                 key=lambda x: x.gross_contribution_pct, reverse=True)

        top_pos = [i.key for i in sorted_by_gross[:3] if i.gross_contribution_pct > 0]
        top_neg = [i.key for i in reversed(sorted_by_gross[-3:]) if i.gross_contribution_pct < 0]

        result = PortfolioAttributionResult(
            result_id=f"attr_{uuid.uuid4().hex[:8]}",
            portfolio_id=snapshot.portfolio_id,
            generated_at=datetime.now(timezone.utc),
            items=ranked_items,
            top_positive_contributors=top_pos,
            top_negative_contributors=top_neg,
            total_gross_return_pct=snapshot.gross_return_pct,
            total_net_return_pct=snapshot.net_return_pct,
            total_cost_drag_pct=snapshot.total_cost_drag_pct,
            status=snapshot.status
        )
        return result

    def symbol_attribution(self, snapshot: PortfolioValuationSnapshot) -> list[PortfolioAttributionItem]:
        items = []
        for pos in snapshot.positions:
            gross = pos.contribution_to_return_pct

            # Approximate net contribution
            cost_bps = pos.estimated_cost_bps or 0.0
            slip_bps = pos.estimated_slippage_bps or 0.0
            cost_drag = (cost_bps + slip_bps) / 10000.0 * pos.current_weight * 100.0

            net = (gross - cost_drag) if gross is not None else None

            item = PortfolioAttributionItem(
                attribution_id=f"item_{uuid.uuid4().hex[:8]}",
                portfolio_id=snapshot.portfolio_id,
                attribution_type=AttributionType.SYMBOL,
                key=pos.symbol,
                gross_contribution_pct=gross,
                net_contribution_pct=net,
                risk_contribution_pct=pos.contribution_to_risk_pct,
                cost_contribution_pct=cost_drag,
                weight=pos.current_weight,
                message=f"Contribution for symbol {pos.symbol}"
            )
            items.append(item)
        return items

    def sector_attribution(self, snapshot: PortfolioValuationSnapshot) -> list[PortfolioAttributionItem]:
        sector_gross = defaultdict(float)
        sector_net = defaultdict(float)
        sector_weight = defaultdict(float)
        sector_cost = defaultdict(float)

        for pos in snapshot.positions:
            sec = pos.sector or "UNKNOWN"
            sector_weight[sec] += pos.current_weight

            if pos.contribution_to_return_pct is not None:
                sector_gross[sec] += pos.contribution_to_return_pct

                cost_bps = pos.estimated_cost_bps or 0.0
                slip_bps = pos.estimated_slippage_bps or 0.0
                drag = (cost_bps + slip_bps) / 10000.0 * pos.current_weight * 100.0

                sector_cost[sec] += drag
                sector_net[sec] += (pos.contribution_to_return_pct - drag)

        items = []
        for sec in sector_weight.keys():
            items.append(PortfolioAttributionItem(
                attribution_id=f"item_{uuid.uuid4().hex[:8]}",
                portfolio_id=snapshot.portfolio_id,
                attribution_type=AttributionType.SECTOR,
                key=sec,
                gross_contribution_pct=sector_gross.get(sec),
                net_contribution_pct=sector_net.get(sec),
                cost_contribution_pct=sector_cost.get(sec),
                weight=sector_weight.get(sec),
                message=f"Contribution for sector {sec}"
            ))
        return items

    def strategy_attribution(self, snapshot: PortfolioValuationSnapshot) -> list[PortfolioAttributionItem]:
        strat_gross = defaultdict(float)
        strat_net = defaultdict(float)
        strat_weight = defaultdict(float)
        strat_cost = defaultdict(float)

        for pos in snapshot.positions:
            strat = pos.strategy_name or "UNKNOWN"
            strat_weight[strat] += pos.current_weight

            if pos.contribution_to_return_pct is not None:
                strat_gross[strat] += pos.contribution_to_return_pct

                cost_bps = pos.estimated_cost_bps or 0.0
                slip_bps = pos.estimated_slippage_bps or 0.0
                drag = (cost_bps + slip_bps) / 10000.0 * pos.current_weight * 100.0

                strat_cost[strat] += drag
                strat_net[strat] += (pos.contribution_to_return_pct - drag)

        items = []
        for strat in strat_weight.keys():
            items.append(PortfolioAttributionItem(
                attribution_id=f"item_{uuid.uuid4().hex[:8]}",
                portfolio_id=snapshot.portfolio_id,
                attribution_type=AttributionType.STRATEGY,
                key=strat,
                gross_contribution_pct=strat_gross.get(strat),
                net_contribution_pct=strat_net.get(strat),
                cost_contribution_pct=strat_cost.get(strat),
                weight=strat_weight.get(strat),
                message=f"Contribution for strategy {strat}"
            ))
        return items

    def cost_attribution(self, snapshot: PortfolioValuationSnapshot) -> list[PortfolioAttributionItem]:
        # Cost drag is a negative contribution to the portfolio.
        # This breaks it down by symbol for clarity.
        items = []
        for pos in snapshot.positions:
            cost_bps = pos.estimated_cost_bps or 0.0
            slip_bps = pos.estimated_slippage_bps or 0.0
            cost_drag = (cost_bps + slip_bps) / 10000.0 * pos.current_weight * 100.0

            item = PortfolioAttributionItem(
                attribution_id=f"item_{uuid.uuid4().hex[:8]}",
                portfolio_id=snapshot.portfolio_id,
                attribution_type=AttributionType.COST,
                key=pos.symbol,
                gross_contribution_pct=0.0,
                net_contribution_pct=-cost_drag,
                cost_contribution_pct=cost_drag,
                weight=pos.current_weight,
                message=f"Cost drag for symbol {pos.symbol}"
            )
            items.append(item)
        return items

    def risk_budget_attribution(self, snapshot: PortfolioValuationSnapshot) -> list[PortfolioAttributionItem]:
        items = []
        for pos in snapshot.positions:
            if pos.contribution_to_risk_pct is not None:
                item = PortfolioAttributionItem(
                    attribution_id=f"item_{uuid.uuid4().hex[:8]}",
                    portfolio_id=snapshot.portfolio_id,
                    attribution_type=AttributionType.RISK_BUDGET,
                    key=pos.symbol,
                    risk_contribution_pct=pos.contribution_to_risk_pct,
                    weight=pos.current_weight,
                    message=f"Risk contribution for symbol {pos.symbol}"
                )
                items.append(item)
        return items

    def rank_contributors(self, items: list[PortfolioAttributionItem]) -> list[PortfolioAttributionItem]:
        valid_items = [i for i in items if i.gross_contribution_pct is not None]
        invalid_items = [i for i in items if i.gross_contribution_pct is None]

        valid_items.sort(key=lambda x: x.gross_contribution_pct, reverse=True)

        for rank, item in enumerate(valid_items, start=1):
            item.rank = rank

        return valid_items + invalid_items
