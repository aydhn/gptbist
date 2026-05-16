import uuid
from datetime import datetime, timezone

from bist_signal_bot.adaptive.models import (
    AdaptivePolicy,
    AdaptiveStrategyCandidate,
    AdaptiveEvidence,
    AdaptiveRefreshPlan,
    AdaptiveRefreshPlanItem,
    AdaptiveRefreshAction,
    AdaptiveDecisionStatus
)

class AdaptiveRefreshPlanner:
    def build_refresh_plan(self, candidates: list[AdaptiveStrategyCandidate], evidence_items: list[AdaptiveEvidence], policy: AdaptivePolicy) -> AdaptiveRefreshPlan:
        items = []
        for candidate in candidates:
            if candidate.status == AdaptiveDecisionStatus.INSUFFICIENT_EVIDENCE:
                items.append(
                    AdaptiveRefreshPlanItem(
                        action=AdaptiveRefreshAction.RUN_BACKTEST,
                        symbol=candidate.symbol,
                        strategy_name=candidate.strategy_name,
                        reason="Insufficient evidence to make recommendation",
                        priority=10,
                        safe_to_auto_run=True,
                        command_preview=self.command_for_action(AdaptiveRefreshAction.RUN_BACKTEST, candidate.symbol, candidate.strategy_name)
                    )
                )
            elif candidate.status == AdaptiveDecisionStatus.NEEDS_REFRESH:
                items.append(
                    AdaptiveRefreshPlanItem(
                        action=AdaptiveRefreshAction.RUN_OPTIMIZATION,
                        symbol=candidate.symbol,
                        strategy_name=candidate.strategy_name,
                        reason="Performance degradation detected",
                        priority=8,
                        safe_to_auto_run=False,
                        command_preview=self.command_for_action(AdaptiveRefreshAction.RUN_OPTIMIZATION, candidate.symbol, candidate.strategy_name)
                    )
                )
            elif "HIGH_OVERFIT_RISK" in candidate.warnings:
                items.append(
                    AdaptiveRefreshPlanItem(
                        action=AdaptiveRefreshAction.RUN_WALK_FORWARD,
                        symbol=candidate.symbol,
                        strategy_name=candidate.strategy_name,
                        reason="High overfit risk detected",
                        priority=9,
                        safe_to_auto_run=False,
                        command_preview=self.command_for_action(AdaptiveRefreshAction.RUN_WALK_FORWARD, candidate.symbol, candidate.strategy_name)
                    )
                )
            elif candidate.status == AdaptiveDecisionStatus.WATCH_ONLY:
                items.append(
                    AdaptiveRefreshPlanItem(
                        action=AdaptiveRefreshAction.WATCH_ONLY,
                        symbol=candidate.symbol,
                        strategy_name=candidate.strategy_name,
                        reason="Strategy on watch list",
                        priority=5,
                        safe_to_auto_run=True,
                        command_preview=[]
                    )
                )

        items = self.prioritize_items(items)

        return AdaptiveRefreshPlan(
            plan_id=f"plan_{uuid.uuid4().hex[:8]}",
            items=items,
            generated_at=datetime.now(timezone.utc),
            status=AdaptiveDecisionStatus.APPROVED_RESEARCH if items else AdaptiveDecisionStatus.SKIPPED
        )

    def command_for_action(self, action: AdaptiveRefreshAction, symbol: str | None = None, strategy_name: str | None = None) -> list[str]:
        base = ["python", "-m", "bist_signal_bot"]
        sym_args = ["--symbols", symbol] if symbol else []
        strat_args = ["--strategy", strategy_name] if strategy_name else []

        if action == AdaptiveRefreshAction.RUN_BACKTEST:
            return base + ["backtest", "run"] + sym_args + strat_args
        elif action == AdaptiveRefreshAction.RUN_OPTIMIZATION:
            return base + ["optimize", "strategy"] + sym_args + strat_args
        elif action == AdaptiveRefreshAction.RUN_WALK_FORWARD:
            return base + ["optimize", "walk-forward"] + sym_args + strat_args
        elif action == AdaptiveRefreshAction.REFRESH_PARAMETERS:
            return base + ["adaptive", "apply-params", "--confirm"]
        elif action == AdaptiveRefreshAction.RETRAIN_MODEL:
            return base + ["ml-train", "train"] + sym_args
        elif action == AdaptiveRefreshAction.REDUCE_UNIVERSE:
            return base + ["runtime", "config", "--reduce-universe"]
        elif action == AdaptiveRefreshAction.LOWER_RISK:
            return base + ["risk", "config", "--lower-risk"]

        return []

    def prioritize_items(self, items: list[AdaptiveRefreshPlanItem]) -> list[AdaptiveRefreshPlanItem]:
        return sorted(items, key=lambda x: x.priority, reverse=True)
