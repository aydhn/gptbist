import pandas as pd
from typing import List, Dict, Optional
import uuid
import numpy as np

from bist_signal_bot.portfolio_construction.models import RiskBudgetItem

class RiskBudgetCalculator:
    def calculate_risk_budget(self, weights: Dict[str, float], returns_df: pd.DataFrame) -> List[RiskBudgetItem]:
        items = []
        contrib = self.contribution_to_risk(weights, returns_df)
        volatilities = self.volatility_by_symbol(returns_df)

        for sym, weight in weights.items():
            items.append(RiskBudgetItem(
                item_id=f"rb_{uuid.uuid4().hex[:8]}",
                symbol=sym,
                target_weight=weight,
                volatility_pct=volatilities.get(sym, 0.0) * 100,
                contribution_to_risk_pct=(contrib.get(sym) or 0.0) * 100
            ))
        return items

    def volatility_by_symbol(self, returns_df: pd.DataFrame) -> Dict[str, float]:
        if returns_df.empty:
            return {}
        vols = returns_df.std() * np.sqrt(252)
        return vols.fillna(0.0).to_dict()

    def portfolio_volatility(self, weights: Dict[str, float], returns_df: pd.DataFrame) -> Optional[float]:
        if returns_df.empty or not weights:
            return None

        syms = [s for s in weights.keys() if s in returns_df.columns]
        if not syms:
            return None

        w = np.array([weights[s] for s in syms])
        cov = returns_df[syms].cov() * 252
        port_var = np.dot(w.T, np.dot(cov, w))
        return float(np.sqrt(max(0, port_var)))

    def contribution_to_risk(self, weights: Dict[str, float], returns_df: pd.DataFrame) -> Dict[str, Optional[float]]:
        if returns_df.empty or not weights:
            return {s: None for s in weights}

        syms = [s for s in weights.keys() if s in returns_df.columns]
        if not syms:
            return {s: None for s in weights}

        w = np.array([weights[s] for s in syms])
        cov = returns_df[syms].cov() * 252

        port_var = np.dot(w.T, np.dot(cov, w))
        if port_var <= 0:
            return {s: 0.0 for s in weights}

        marginal_risk = np.dot(cov, w) / np.sqrt(port_var)
        ctr = (w * marginal_risk) / np.sqrt(port_var)

        result = {s: None for s in weights}
        for i, s in enumerate(syms):
            result[s] = float(ctr[i])
        return result

    def risk_budget_gaps(self, items: List[RiskBudgetItem], target_budget: Optional[Dict[str, float]] = None) -> List[RiskBudgetItem]:
        for item in items:
            if target_budget and item.symbol in target_budget:
                target = target_budget[item.symbol]
                item.risk_budget_pct = target * 100
                if item.contribution_to_risk_pct is not None:
                    item.budget_gap_pct = item.contribution_to_risk_pct - item.risk_budget_pct
        return items
