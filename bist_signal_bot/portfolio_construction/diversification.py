from typing import List, Optional, Dict
import numpy as np

from bist_signal_bot.portfolio_construction.models import PortfolioPositionResearch, CorrelationCluster
from bist_signal_bot.config.settings import Settings

class DiversificationScorer:
    def __init__(self, settings: Settings):
        self.settings = settings

    def score_diversification(self, positions: List[PortfolioPositionResearch], corr_clusters: Optional[List[CorrelationCluster]] = None) -> Optional[float]:
        if not positions:
            return 0.0

        concentration_score = self.symbol_concentration_score(positions) or 0.0
        sector_score = self.sector_diversification_score(positions) or 0.0

        base_score = (concentration_score + sector_score) / 2.0

        penalty = 0.0
        if corr_clusters:
            penalty = self.correlation_penalty(corr_clusters) or 0.0

        return max(0.0, min(100.0, base_score - penalty))

    def sector_diversification_score(self, positions: List[PortfolioPositionResearch]) -> Optional[float]:
        if not positions:
            return None

        sectors = {}
        for p in positions:
            s = p.sector or "UNKNOWN"
            sectors[s] = sectors.get(s, 0.0) + p.target_weight

        hhi = sum(w**2 for w in sectors.values())
        if hhi <= 0:
            return 100.0

        score = max(0.0, 100.0 * (1.0 - hhi))
        return score

    def symbol_concentration_score(self, positions: List[PortfolioPositionResearch]) -> Optional[float]:
        if not positions:
            return None

        weights = {p.symbol: p.target_weight for p in positions}
        eff_n = self.effective_number_of_positions(weights)
        if eff_n is None or eff_n <= 0:
            return 0.0

        score = (eff_n / len(positions)) * 100.0
        return min(100.0, score)

    def correlation_penalty(self, clusters: List[CorrelationCluster]) -> Optional[float]:
        if not clusters:
            return 0.0
        max_cluster_weight = max((c.cluster_weight or 0.0) for c in clusters)
        if max_cluster_weight > self.settings.PORTFOLIO_MAX_CORRELATION_CLUSTER_WEIGHT:
            return 20.0
        return 0.0

    def effective_number_of_positions(self, weights: Dict[str, float]) -> Optional[float]:
        total = sum(weights.values())
        if total <= 0:
            return None

        hhi = sum((w/total)**2 for w in weights.values())
        if hhi <= 0:
            return None

        return 1.0 / hhi
