import uuid
from datetime import datetime
from bist_signal_bot.portfolio_research.models import (
    ResearchPortfolioSnapshot,
    ResearchPortfolioItem,
    RebalancePlan,
    RebalancePlanItem,
    RebalanceDecision
)

class RebalancePlanner:

    def build_plan(self, current: ResearchPortfolioSnapshot | None, target: ResearchPortfolioSnapshot) -> RebalancePlan:
        current_items = current.items if current else []
        plan_items = self.compare_weights(current_items, target.items)

        # We can filter small deltas if configured externally, for now just compute turnover
        turnover = self.estimate_turnover(plan_items)

        plan = RebalancePlan(
            plan_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            current_snapshot_id=current.snapshot_id if current else None,
            target_snapshot_id=target.snapshot_id,
            items=plan_items,
            turnover_estimate=turnover,
            add_count=sum(1 for i in plan_items if i.decision == RebalanceDecision.ADD_RESEARCH),
            remove_count=sum(1 for i in plan_items if i.decision == RebalanceDecision.REMOVE_RESEARCH),
            increase_count=sum(1 for i in plan_items if i.decision == RebalanceDecision.INCREASE_RESEARCH_WEIGHT),
            decrease_count=sum(1 for i in plan_items if i.decision == RebalanceDecision.DECREASE_RESEARCH_WEIGHT),
            no_change_count=sum(1 for i in plan_items if i.decision == RebalanceDecision.NO_CHANGE)
        )

        if turnover > 0.5:
            plan.warnings.append(f"High research turnover estimated: {turnover:.2%}")

        return plan

    def compare_weights(self, current_items: list[ResearchPortfolioItem], target_items: list[ResearchPortfolioItem]) -> list[RebalancePlanItem]:
        current_map = {i.symbol: i for i in current_items if i.final_weight > 0}
        target_map = {i.symbol: i for i in target_items if i.final_weight > 0}

        all_symbols = set(current_map.keys()) | set(target_map.keys())

        plan_items = []
        for sym in all_symbols:
            c_w = current_map[sym].final_weight if sym in current_map else 0.0
            t_w = target_map[sym].final_weight if sym in target_map else 0.0
            delta = t_w - c_w

            decision = RebalanceDecision.NO_CHANGE
            if c_w == 0 and t_w > 0:
                decision = RebalanceDecision.ADD_RESEARCH
            elif c_w > 0 and t_w == 0:
                decision = RebalanceDecision.REMOVE_RESEARCH
            elif delta > 1e-4:
                decision = RebalanceDecision.INCREASE_RESEARCH_WEIGHT
            elif delta < -1e-4:
                decision = RebalanceDecision.DECREASE_RESEARCH_WEIGHT

            plan_items.append(RebalancePlanItem(
                plan_item_id=str(uuid.uuid4()),
                symbol=sym,
                current_weight=c_w,
                target_weight=t_w,
                delta_weight=delta,
                decision=decision,
                reason=self.build_rebalance_reason(current_map.get(sym), target_map.get(sym))
            ))

        return plan_items

    def estimate_turnover(self, items: list[RebalancePlanItem]) -> float:
        # Simple turnover estimate: sum of absolute weight changes divided by 2
        total_delta = sum(abs(i.delta_weight) for i in items)
        return total_delta / 2.0

    def filter_small_deltas(self, items: list[RebalancePlanItem], min_delta_weight: float) -> list[RebalancePlanItem]:
        filtered = []
        for i in items:
            if abs(i.delta_weight) >= min_delta_weight or i.decision in (RebalanceDecision.ADD_RESEARCH, RebalanceDecision.REMOVE_RESEARCH):
                filtered.append(i)
            else:
                i.decision = RebalanceDecision.NO_CHANGE
                i.delta_weight = 0.0
                i.target_weight = i.current_weight
                i.reason = f"Delta < min_delta ({min_delta_weight}), skipped"
                filtered.append(i)
        return filtered

    def build_rebalance_reason(self, current_item: ResearchPortfolioItem | None, target_item: ResearchPortfolioItem | None) -> str:
        if current_item and not target_item:
            return "Removed from target research portfolio"
        if not current_item and target_item:
            return "Added to target research portfolio"
        if current_item and target_item:
            if current_item.final_weight != target_item.final_weight:
                return f"Weight adjusted from {current_item.final_weight:.2%} to {target_item.final_weight:.2%}"
            return "No weight change"
        return "Unknown"
