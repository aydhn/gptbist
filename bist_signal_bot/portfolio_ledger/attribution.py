from datetime import datetime, timezone
import uuid
from typing import Any, Callable
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

    def _group_attribution(self, snapshot: PortfolioValuationSnapshot, group_key_func: Callable[[Any], str], attribution_type: AttributionType, message_template: str) -> list[PortfolioAttributionItem]:
        group_gross = defaultdict(float)
        group_net = defaultdict(float)
        group_weight = defaultdict(float)
        group_cost = defaultdict(float)

        for pos in snapshot.positions:
            key = group_key_func(pos)
            group_weight[key] += pos.current_weight

            if pos.contribution_to_return_pct is not None:
                group_gross[key] += pos.contribution_to_return_pct

                cost_bps = pos.estimated_cost_bps or 0.0
                slip_bps = pos.estimated_slippage_bps or 0.0
                drag = (cost_bps + slip_bps) / 10000.0 * pos.current_weight * 100.0

                group_cost[key] += drag
                group_net[key] += (pos.contribution_to_return_pct - drag)

        items = []
        for key in group_weight.keys():
            items.append(PortfolioAttributionItem(
                attribution_id=f"item_{uuid.uuid4().hex[:8]}",
                portfolio_id=snapshot.portfolio_id,
                attribution_type=attribution_type,
                key=key,
                gross_contribution_pct=group_gross.get(key),
                net_contribution_pct=group_net.get(key),
                cost_contribution_pct=group_cost.get(key),
                weight=group_weight.get(key),
                message=message_template.format(key=key)
            ))
        return items

    def sector_attribution(self, snapshot: PortfolioValuationSnapshot) -> list[PortfolioAttributionItem]:
        return self._group_attribution(
            snapshot,
            lambda pos: pos.sector or "UNKNOWN",
            AttributionType.SECTOR,
            "Contribution for sector {key}"
        )

    def strategy_attribution(self, snapshot: PortfolioValuationSnapshot) -> list[PortfolioAttributionItem]:
        return self._group_attribution(
            snapshot,
            lambda pos: pos.strategy_name or "UNKNOWN",
            AttributionType.STRATEGY,
            "Contribution for strategy {key}"
        )

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
