from typing import List, Dict, Optional
import pandas as pd
import numpy as np

from bist_signal_bot.portfolio_construction.models import (
    PortfolioCandidate, PortfolioConstructionRequest, PortfolioWeightingMethod
)
from bist_signal_bot.config.settings import Settings

class PortfolioWeightingEngine:
    def __init__(self, settings: Settings):
        self.settings = settings

    def build_weights(self, candidates: List[PortfolioCandidate], request: PortfolioConstructionRequest, returns_df: Optional[pd.DataFrame] = None) -> Dict[str, float]:
        if not candidates:
            return {}

        method = request.weighting_method
        max_pos = request.max_positions

        if method == PortfolioWeightingMethod.EQUAL_WEIGHT:
            weights = self.equal_weight(candidates, max_pos)
        elif method == PortfolioWeightingMethod.CONFIDENCE_WEIGHTED:
            weights = self.confidence_weighted(candidates, max_pos)
        elif method == PortfolioWeightingMethod.SCORE_WEIGHTED:
            weights = self.score_weighted(candidates, max_pos)
        elif method == PortfolioWeightingMethod.RISK_PARITY_LITE:
            weights = self.risk_parity_lite(candidates, returns_df, max_pos)
        else: # Default HYBRID or CUSTOM fallback to EQUAL_WEIGHT for simplicity here
            weights = self.equal_weight(candidates, max_pos)

        if request.include_liquidity_penalty:
            weights = self.liquidity_adjusted(weights, candidates)

        if request.include_execution_costs:
            weights = self.cost_adjusted(weights, candidates)

        return self.normalize_weights(weights)

    def equal_weight(self, candidates: List[PortfolioCandidate], max_positions: int) -> Dict[str, float]:
        cands = candidates[:max_positions]
        if not cands:
            return {}
        w = 1.0 / len(cands)
        return {c.symbol: w for c in cands}

    def confidence_weighted(self, candidates: List[PortfolioCandidate], max_positions: int) -> Dict[str, float]:
        cands = candidates[:max_positions]
        if not cands:
            return {}

        total = sum((c.calibrated_confidence or c.raw_confidence or 50.0) for c in cands)
        if total <= 0:
            return self.equal_weight(cands, max_positions)

        return {c.symbol: (c.calibrated_confidence or c.raw_confidence or 50.0) / total for c in cands}

    def score_weighted(self, candidates: List[PortfolioCandidate], max_positions: int) -> Dict[str, float]:
        cands = candidates[:max_positions]
        if not cands:
            return {}

        total = sum((c.final_candidate_score or 50.0) for c in cands)
        if total <= 0:
            return self.equal_weight(cands, max_positions)

        return {c.symbol: (c.final_candidate_score or 50.0) / total for c in cands}

    def risk_parity_lite(self, candidates: List[PortfolioCandidate], returns_df: Optional[pd.DataFrame], max_positions: int) -> Dict[str, float]:
        cands = candidates[:max_positions]
        if not cands or returns_df is None or returns_df.empty:
            return self.equal_weight(cands, max_positions)

        syms = [c.symbol for c in cands if c.symbol in returns_df.columns]
        if not syms:
            return self.equal_weight(cands, max_positions)

        vols = returns_df[syms].std() * np.sqrt(252)
        inv_vols = 1.0 / vols.replace(0, np.nan)
        inv_vols = inv_vols.fillna(1.0) # Fallback for 0 volatility

        total_inv_vol = inv_vols.sum()
        if total_inv_vol <= 0:
            return self.equal_weight(cands, max_positions)

        return (inv_vols / total_inv_vol).to_dict()

    def liquidity_adjusted(self, weights: Dict[str, float], candidates: List[PortfolioCandidate]) -> Dict[str, float]:
        return weights

    def cost_adjusted(self, weights: Dict[str, float], candidates: List[PortfolioCandidate]) -> Dict[str, float]:
        return weights

    def normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        total = sum(max(0, w) for w in weights.values())
        if total <= 0:
            return {}
        return {s: max(0, w) / total for s, w in weights.items()}
