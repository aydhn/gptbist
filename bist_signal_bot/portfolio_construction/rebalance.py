from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from bist_signal_bot.portfolio_construction.models import RebalanceSimulation, RebalanceActionType, PortfolioPositionResearch
from bist_signal_bot.config.settings import Settings

class RebalanceSimulator:
    def __init__(self, settings: Settings):
        self.settings = settings

    def simulate(self, current_weights: Dict[str, float], target_weights: Dict[str, float],
                 portfolio_notional: float, positions: Optional[List[PortfolioPositionResearch]] = None) -> RebalanceSimulation:

        actions = self.build_actions(current_weights, target_weights)
        turnover = self.estimate_turnover(current_weights, target_weights)
        cost_estimate = self.estimate_rebalance_cost(actions, portfolio_notional)

        return RebalanceSimulation(
            rebalance_id=f"reb_{uuid.uuid4().hex[:8]}",
            current_weights=current_weights,
            target_weights=target_weights,
            actions=actions,
            estimated_turnover_pct=turnover,
            estimated_cost_bps=cost_estimate.get("cost_bps", 0.0),
            estimated_slippage_bps=cost_estimate.get("slippage_bps", 0.0)
        )

    def build_actions(self, current_weights: Dict[str, float], target_weights: Dict[str, float]) -> List[Dict[str, Any]]:
        all_syms = set(current_weights.keys()).union(set(target_weights.keys()))
        actions = []
        for sym in all_syms:
            cw = current_weights.get(sym, 0.0)
            tw = target_weights.get(sym, 0.0)
            delta = tw - cw

            action_type = self.classify_action(cw, tw)
            if action_type != RebalanceActionType.SKIP:
                actions.append({
                    "symbol": sym,
                    "action": action_type.value,
                    "current_weight": cw,
                    "target_weight": tw,
                    "delta_weight": delta
                })
        return actions

    def estimate_turnover(self, current_weights: Dict[str, float], target_weights: Dict[str, float]) -> float:
        all_syms = set(current_weights.keys()).union(set(target_weights.keys()))
        turnover = 0.0
        for sym in all_syms:
            cw = current_weights.get(sym, 0.0)
            tw = target_weights.get(sym, 0.0)
            turnover += abs(tw - cw)
        return (turnover / 2.0) * 100.0 # One sided turnover

    def estimate_rebalance_cost(self, actions: List[Dict[str, Any]], portfolio_notional: float) -> Dict[str, float]:
        total_traded_notional = sum(abs(a["delta_weight"]) * portfolio_notional for a in actions)
        if portfolio_notional <= 0:
            return {"cost_bps": 0.0, "slippage_bps": 0.0}

        cost_bps = 10.0 * (total_traded_notional / portfolio_notional)
        slippage_bps = 5.0 * (total_traded_notional / portfolio_notional)

        return {
            "cost_bps": cost_bps,
            "slippage_bps": slippage_bps
        }

    def classify_action(self, current_weight: float, target_weight: float) -> RebalanceActionType:
        min_delta = self.settings.PORTFOLIO_REBALANCE_MIN_DELTA_WEIGHT
        delta = target_weight - current_weight

        if current_weight == 0 and target_weight > 0:
            return RebalanceActionType.ADD
        elif current_weight > 0 and target_weight == 0:
            return RebalanceActionType.REMOVE
        elif delta > min_delta:
            return RebalanceActionType.INCREASE
        elif delta < -min_delta:
            return RebalanceActionType.DECREASE
        elif target_weight > 0:
            return RebalanceActionType.HOLD
        else:
            return RebalanceActionType.SKIP
