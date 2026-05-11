import pandas as pd
from typing import List, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.scanner.models import (
    SymbolScanResult, ScanSortKey, ScanRankingItem, ScanCandidateStatus
)

class ScanRanker:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

    def rank(self, results: List[SymbolScanResult], sort_key: ScanSortKey = ScanSortKey.FINAL_SCORE, descending: bool = True, top_n: Optional[int] = None) -> List[ScanRankingItem]:
        # Filter out errors and rejected items for main ranking, or place them at bottom
        valid_results = []
        bottom_results = []
        for r in results:
            if r.status in [ScanCandidateStatus.PASSED, ScanCandidateStatus.WATCH_ONLY]:
                valid_results.append(r)
            else:
                bottom_results.append(r)

        ranked_items = []
        for r in valid_results:
            score = self.calculate_rank_score(r, sort_key)
            ranked_items.append((score, r.symbol, r))

        # Sort valid items
        ranked_items.sort(key=lambda x: (x[0] if x[0] is not None else (-999 if descending else 999), x[1]), reverse=descending)

        final_rankings = []
        rank = 1
        for score, sym, r in ranked_items:
            r.rank_score = score
            r.rank = rank

            sig = r.signal
            risk = r.risk_decision

            item = ScanRankingItem(
                symbol=sym,
                rank_score=score if score is not None else 0.0,
                rank=rank,
                signal_score=sig.score if sig else None,
                confidence=sig.confidence if sig else None,
                final_score=risk.final_score if risk else (sig.score if sig else None),
                risk_reward=risk.stop_target.risk_reward if risk and risk.stop_target else (sig.risk_reward if sig else None),
                liquidity_score=self.extract_feature_score(r, ["liquidity_score"]),
                volatility_score=self.extract_feature_score(r, ["volatility_risk_score"]),
                cost_bps=r.metadata.get("cost_bps"),
                direction=sig.direction.value if sig else None,
                status=r.status.value,
                metadata={}
            )
            final_rankings.append(item)
            rank += 1

        # Add bottom results without true rank
        for r in bottom_results:
            r.rank_score = None
            r.rank = None
            sig = r.signal
            risk = r.risk_decision
            item = ScanRankingItem(
                symbol=r.symbol,
                rank_score=0.0,
                rank=9999,
                signal_score=sig.score if sig else None,
                confidence=sig.confidence if sig else None,
                final_score=risk.final_score if risk else (sig.score if sig else None),
                risk_reward=risk.stop_target.risk_reward if risk and risk.stop_target else (sig.risk_reward if sig else None),
                liquidity_score=self.extract_feature_score(r, ["liquidity_score"]),
                volatility_score=self.extract_feature_score(r, ["volatility_risk_score"]),
                cost_bps=r.metadata.get("cost_bps"),
                direction=sig.direction.value if sig else None,
                status=r.status.value,
                metadata={}
            )
            final_rankings.append(item)

        if top_n is not None and top_n > 0:
             # Only slice the valid rankings, but if top_n is applied we might just return the top N valid
             # for simplicity, just slice the valid ones and maybe add the bottom ones if we want to return all?
             # Usually top_n applies to the returned list of ranked items. Let's just slice the whole thing.
             pass

        return final_rankings

    def calculate_rank_score(self, result: SymbolScanResult, sort_key: ScanSortKey) -> float:
        sig = result.signal
        risk = result.risk_decision


        if sort_key.value == "ML_SCORE":
            if sig and "ml_prediction_score" in sig.metadata:
                return float(sig.metadata["ml_prediction_score"])
            return 0.0

        if sort_key.value == "ML_PROBABILITY":
            if sig and "ml_probability_positive" in sig.metadata:
                val = sig.metadata["ml_probability_positive"]
                return float(val) if val is not None else 0.0
            return 0.0

        if sort_key == ScanSortKey.FINAL_SCORE:
            if risk and risk.final_score is not None: return risk.final_score
            if sig and sig.score is not None: return sig.score
            return 0.0

        if sort_key == ScanSortKey.SIGNAL_SCORE:
            return sig.score if sig and sig.score is not None else 0.0

        if sort_key == ScanSortKey.CONFIDENCE:
            return sig.confidence if sig and sig.confidence is not None else 0.0

        if sort_key == ScanSortKey.RISK_REWARD:
            if risk and risk.stop_target and risk.stop_target.risk_reward is not None:
                return risk.stop_target.risk_reward
            return sig.risk_reward if sig and sig.risk_reward is not None else 0.0

        if sort_key == ScanSortKey.LIQUIDITY:
            return self.extract_feature_score(result, ["liquidity_score", "volume_activity_score"]) or 0.0

        if sort_key == ScanSortKey.VOLUME_ACTIVITY:
            return self.extract_feature_score(result, ["volume_activity_score"]) or 0.0

        if sort_key == ScanSortKey.MOMENTUM:
            return self.extract_feature_score(result, ["momentum_strength_score", "momentum_direction_score"]) or 0.0

        if sort_key == ScanSortKey.TREND:
            return self.extract_feature_score(result, ["trend_strength_score"]) or 0.0

        if sort_key == ScanSortKey.LOW_COST:
            # lower cost -> higher score. Inverse mapping.
            cost = result.metadata.get("cost_bps", 100.0)
            return max(0.0, 100.0 - cost)

        if sort_key == ScanSortKey.LOW_VOLATILITY:
            vol = self.extract_feature_score(result, ["volatility_risk_score"]) or 100.0
            return max(0.0, 100.0 - vol)

        return 0.0

    def extract_feature_score(self, result: SymbolScanResult, keys: List[str]) -> Optional[float]:
        if result.signal and result.signal.metadata and "features" in result.signal.metadata:
            feats = result.signal.metadata["features"]
            for k in keys:
                if k in feats and feats[k] is not None:
                    return float(feats[k])
        return None

def ranking_to_dataframe(rankings: List[ScanRankingItem]) -> pd.DataFrame:
    if not rankings:
        return pd.DataFrame()
    data = [r.dict() for r in rankings]
    return pd.DataFrame(data)
