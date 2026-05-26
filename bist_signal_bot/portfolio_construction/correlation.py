import pandas as pd
from typing import List, Optional, Dict, Any
import uuid

from bist_signal_bot.portfolio_construction.models import CorrelationCluster

class CorrelationAnalyzer:
    def returns_matrix(self, symbols: List[str], lookback_days: int = 120) -> pd.DataFrame:
        import numpy as np
        dates = pd.date_range(end=pd.Timestamp.today(), periods=lookback_days)
        data = np.random.randn(lookback_days, len(symbols)) * 0.01
        return pd.DataFrame(data, index=dates, columns=symbols)

    def correlation_matrix(self, returns_df: pd.DataFrame) -> pd.DataFrame:
        if returns_df.empty:
            return pd.DataFrame()
        return returns_df.corr().fillna(0.0)

    def pairwise_high_correlations(self, corr: pd.DataFrame, threshold: float) -> List[Dict[str, Any]]:
        pairs = []
        if corr.empty:
            return pairs
        for i in range(len(corr.columns)):
            for j in range(i + 1, len(corr.columns)):
                val = corr.iloc[i, j]
                if abs(val) >= threshold:
                    pairs.append({
                        "symbol1": corr.columns[i],
                        "symbol2": corr.columns[j],
                        "correlation": val
                    })
        return pairs

    def build_clusters(self, corr: pd.DataFrame, weights: Dict[str, float], threshold: float) -> List[CorrelationCluster]:
        clusters = []
        visited = set()
        for sym in corr.columns:
            if sym in visited:
                continue
            cluster_syms = [sym]
            visited.add(sym)
            for other_sym in corr.columns:
                if other_sym not in visited and abs(corr.loc[sym, other_sym]) >= threshold:
                    cluster_syms.append(other_sym)
                    visited.add(other_sym)

            if len(cluster_syms) > 1:
                cluster_weight = sum(weights.get(s, 0.0) for s in cluster_syms)
                clusters.append(CorrelationCluster(
                    cluster_id=f"clust_{uuid.uuid4().hex[:8]}",
                    symbols=cluster_syms,
                    cluster_weight=cluster_weight
                ))
        return clusters

    def average_portfolio_correlation(self, corr: pd.DataFrame, weights: Dict[str, float]) -> Optional[float]:
        if corr.empty or not weights:
            return None

        total_weight = sum(weights.values())
        if total_weight <= 0:
            return None

        avg_corr = 0.0
        pairs = 0
        syms = list(weights.keys())
        for i in range(len(syms)):
            for j in range(i + 1, len(syms)):
                s1, s2 = syms[i], syms[j]
                if s1 in corr.columns and s2 in corr.columns:
                    w1 = weights[s1] / total_weight
                    w2 = weights[s2] / total_weight
                    avg_corr += corr.loc[s1, s2] * w1 * w2
                    pairs += 1
        return avg_corr if pairs > 0 else 0.0
