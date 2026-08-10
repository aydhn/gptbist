from typing import List, Optional, TYPE_CHECKING

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.scanner.models import (
    SymbolScanResult,
    ScanSortKey,
    ScanRankingItem,
    ScanCandidateStatus,
)

if TYPE_CHECKING:
    import pandas as pd

class ScanRanker:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

    def rank(
        self,
        results: List[SymbolScanResult],
        sort_key: ScanSortKey = ScanSortKey.FINAL_SCORE,
        descending: bool = True,
        top_n: Optional[int] = None,
    ) -> List[ScanRankingItem]:
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
        ranked_items.sort(
            key=lambda x: (x[0] if x[0] is not None else (-999 if descending else 999), x[1]),
            reverse=descending,
        )

        final_rankings = []
        for rank, (score, sym, r) in enumerate(ranked_items, start=1):
            r.rank_score = score
            r.rank = rank
            final_rankings.append(self._build_ranking_item(r, rank, score))

        # Add bottom results without true rank
        for r in bottom_results:
            r.rank_score = None
            r.rank = None
            final_rankings.append(self._build_ranking_item(r, 9999, 0.0))

        return final_rankings

    def _build_ranking_item(
        self, r: SymbolScanResult, rank: int, rank_score: Optional[float]
    ) -> ScanRankingItem:
        sig = r.signal
        risk = r.risk_decision
        return ScanRankingItem(
            symbol=r.symbol,
            rank_score=rank_score if rank_score is not None else 0.0,
            rank=rank,
            signal_score=sig.score if sig else None,
            confidence=sig.confidence if sig else None,
            final_score=risk.final_score if risk else (sig.score if sig else None),
            risk_reward=risk.stop_target.risk_reward
            if risk and risk.stop_target
            else (sig.risk_reward if sig else None),
            liquidity_score=self.extract_feature_score(r, ["liquidity_score"]),
            volatility_score=self.extract_feature_score(r, ["volatility_risk_score"]),
            cost_bps=r.metadata.get("cost_bps"),
            direction=sig.direction.value if sig else None,
            status=r.status.value,
            metadata={},
        )


    def _score_ml(self, result: SymbolScanResult) -> float:
        if not result.signal: return 0.0
        return float(result.signal.metadata.get("ml_prediction_score", 0.0))

    def _score_ml_prob(self, result: SymbolScanResult) -> float:
        if not result.signal: return 0.0
        val = result.signal.metadata.get("ml_probability_positive")
        return float(val) if val is not None else 0.0

    def _score_final(self, result: SymbolScanResult) -> float:
        if result.risk_decision and getattr(result.risk_decision, "final_score", None) is not None:
            return result.risk_decision.final_score
        if result.signal and getattr(result.signal, "score", None) is not None:
            return result.signal.score
        return 0.0

    def _score_signal(self, result: SymbolScanResult) -> float:
        if result.signal and getattr(result.signal, "score", None) is not None:
            return result.signal.score
        return 0.0

    def _score_confidence(self, result: SymbolScanResult) -> float:
        if result.signal and getattr(result.signal, "confidence", None) is not None:
            return result.signal.confidence
        return 0.0

    def _score_risk_reward(self, result: SymbolScanResult) -> float:
        if result.risk_decision and getattr(result.risk_decision, "stop_target", None):
            if getattr(result.risk_decision.stop_target, "risk_reward", None) is not None:
                return result.risk_decision.stop_target.risk_reward
        if result.signal and getattr(result.signal, "risk_reward", None) is not None:
            return result.signal.risk_reward
        return 0.0

    def _score_liquidity(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["liquidity_score", "volume_activity_score"]) or 0.0

    def _score_volume_activity(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["volume_activity_score"]) or 0.0

    def _score_momentum(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["momentum_strength_score", "momentum_direction_score"]) or 0.0

    def _score_trend(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["trend_strength_score"]) or 0.0

    def _score_low_cost(self, result: SymbolScanResult) -> float:
        return max(0.0, 100.0 - result.metadata.get("cost_bps", 100.0))

    def _score_low_volatility(self, result: SymbolScanResult) -> float:
        return max(0.0, 100.0 - (self.extract_feature_score(result, ["volatility_risk_score"]) or 100.0))

    _SCORE_HANDLERS = {
        "ML_SCORE": _score_ml,
        "ML_PROBABILITY": _score_ml_prob,
        "FINAL_SCORE": _score_final,
        "SIGNAL_SCORE": _score_signal,
        "CONFIDENCE": _score_confidence,
        "RISK_REWARD": _score_risk_reward,
        "LIQUIDITY": _score_liquidity,
        "VOLUME_ACTIVITY": _score_volume_activity,
        "MOMENTUM": _score_momentum,
        "TREND": _score_trend,
        "LOW_COST": _score_low_cost,
        "LOW_VOLATILITY": _score_low_volatility,
    }


    def _score_ml(self, result: SymbolScanResult) -> float:
        if not result.signal: return 0.0
        return float(result.signal.metadata.get("ml_prediction_score", 0.0))

    def _score_ml_prob(self, result: SymbolScanResult) -> float:
        if not result.signal: return 0.0
        val = result.signal.metadata.get("ml_probability_positive")
        return float(val) if val is not None else 0.0

    def _score_final(self, result: SymbolScanResult) -> float:
        if result.risk_decision and getattr(result.risk_decision, "final_score", None) is not None:
            return result.risk_decision.final_score
        if result.signal and getattr(result.signal, "score", None) is not None:
            return result.signal.score
        return 0.0

    def _score_signal(self, result: SymbolScanResult) -> float:
        if result.signal and getattr(result.signal, "score", None) is not None:
            return result.signal.score
        return 0.0

    def _score_confidence(self, result: SymbolScanResult) -> float:
        if result.signal and getattr(result.signal, "confidence", None) is not None:
            return result.signal.confidence
        return 0.0

    def _score_risk_reward(self, result: SymbolScanResult) -> float:
        if result.risk_decision and getattr(result.risk_decision, "stop_target", None):
            if getattr(result.risk_decision.stop_target, "risk_reward", None) is not None:
                return result.risk_decision.stop_target.risk_reward
        if result.signal and getattr(result.signal, "risk_reward", None) is not None:
            return result.signal.risk_reward
        return 0.0

    def _score_liquidity(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["liquidity_score", "volume_activity_score"]) or 0.0

    def _score_volume_activity(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["volume_activity_score"]) or 0.0

    def _score_momentum(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["momentum_strength_score", "momentum_direction_score"]) or 0.0

    def _score_trend(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["trend_strength_score"]) or 0.0

    def _score_low_cost(self, result: SymbolScanResult) -> float:
        return max(0.0, 100.0 - result.metadata.get("cost_bps", 100.0))

    def _score_low_volatility(self, result: SymbolScanResult) -> float:
        return max(0.0, 100.0 - (self.extract_feature_score(result, ["volatility_risk_score"]) or 100.0))

    _SCORE_HANDLERS = {
        "ML_SCORE": _score_ml,
        "ML_PROBABILITY": _score_ml_prob,
        "FINAL_SCORE": _score_final,
        "SIGNAL_SCORE": _score_signal,
        "CONFIDENCE": _score_confidence,
        "RISK_REWARD": _score_risk_reward,
        "LIQUIDITY": _score_liquidity,
        "VOLUME_ACTIVITY": _score_volume_activity,
        "MOMENTUM": _score_momentum,
        "TREND": _score_trend,
        "LOW_COST": _score_low_cost,
        "LOW_VOLATILITY": _score_low_volatility,
    }


    def _score_ml(self, result: SymbolScanResult) -> float:
        if not result.signal: return 0.0
        return float(result.signal.metadata.get("ml_prediction_score", 0.0))

    def _score_ml_prob(self, result: SymbolScanResult) -> float:
        if not result.signal: return 0.0
        val = result.signal.metadata.get("ml_probability_positive")
        return float(val) if val is not None else 0.0

    def _score_final(self, result: SymbolScanResult) -> float:
        if result.risk_decision and getattr(result.risk_decision, "final_score", None) is not None:
            return result.risk_decision.final_score
        if result.signal and getattr(result.signal, "score", None) is not None:
            return result.signal.score
        return 0.0

    def _score_signal(self, result: SymbolScanResult) -> float:
        if result.signal and getattr(result.signal, "score", None) is not None:
            return result.signal.score
        return 0.0

    def _score_confidence(self, result: SymbolScanResult) -> float:
        if result.signal and getattr(result.signal, "confidence", None) is not None:
            return result.signal.confidence
        return 0.0

    def _score_risk_reward(self, result: SymbolScanResult) -> float:
        if result.risk_decision and getattr(result.risk_decision, "stop_target", None):
            if getattr(result.risk_decision.stop_target, "risk_reward", None) is not None:
                return result.risk_decision.stop_target.risk_reward
        if result.signal and getattr(result.signal, "risk_reward", None) is not None:
            return result.signal.risk_reward
        return 0.0

    def _score_liquidity(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["liquidity_score", "volume_activity_score"]) or 0.0

    def _score_volume_activity(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["volume_activity_score"]) or 0.0

    def _score_momentum(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["momentum_strength_score", "momentum_direction_score"]) or 0.0

    def _score_trend(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["trend_strength_score"]) or 0.0

    def _score_low_cost(self, result: SymbolScanResult) -> float:
        return max(0.0, 100.0 - result.metadata.get("cost_bps", 100.0))

    def _score_low_volatility(self, result: SymbolScanResult) -> float:
        return max(0.0, 100.0 - (self.extract_feature_score(result, ["volatility_risk_score"]) or 100.0))

    _SCORE_HANDLERS = {
        "ML_SCORE": _score_ml,
        "ML_PROBABILITY": _score_ml_prob,
        "FINAL_SCORE": _score_final,
        "SIGNAL_SCORE": _score_signal,
        "CONFIDENCE": _score_confidence,
        "RISK_REWARD": _score_risk_reward,
        "LIQUIDITY": _score_liquidity,
        "VOLUME_ACTIVITY": _score_volume_activity,
        "MOMENTUM": _score_momentum,
        "TREND": _score_trend,
        "LOW_COST": _score_low_cost,
        "LOW_VOLATILITY": _score_low_volatility,
    }


    def _score_ml(self, result: SymbolScanResult) -> float:
        if not result.signal: return 0.0
        return float(result.signal.metadata.get("ml_prediction_score", 0.0))

    def _score_ml_prob(self, result: SymbolScanResult) -> float:
        if not result.signal: return 0.0
        val = result.signal.metadata.get("ml_probability_positive")
        return float(val) if val is not None else 0.0

    def _score_final(self, result: SymbolScanResult) -> float:
        if result.risk_decision and getattr(result.risk_decision, "final_score", None) is not None:
            return result.risk_decision.final_score
        if result.signal and getattr(result.signal, "score", None) is not None:
            return result.signal.score
        return 0.0

    def _score_signal(self, result: SymbolScanResult) -> float:
        if result.signal and getattr(result.signal, "score", None) is not None:
            return result.signal.score
        return 0.0

    def _score_confidence(self, result: SymbolScanResult) -> float:
        if result.signal and getattr(result.signal, "confidence", None) is not None:
            return result.signal.confidence
        return 0.0

    def _score_risk_reward(self, result: SymbolScanResult) -> float:
        if result.risk_decision and getattr(result.risk_decision, "stop_target", None):
            if getattr(result.risk_decision.stop_target, "risk_reward", None) is not None:
                return result.risk_decision.stop_target.risk_reward
        if result.signal and getattr(result.signal, "risk_reward", None) is not None:
            return result.signal.risk_reward
        return 0.0

    def _score_liquidity(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["liquidity_score", "volume_activity_score"]) or 0.0

    def _score_volume_activity(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["volume_activity_score"]) or 0.0

    def _score_momentum(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["momentum_strength_score", "momentum_direction_score"]) or 0.0

    def _score_trend(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["trend_strength_score"]) or 0.0

    def _score_low_cost(self, result: SymbolScanResult) -> float:
        return max(0.0, 100.0 - result.metadata.get("cost_bps", 100.0))

    def _score_low_volatility(self, result: SymbolScanResult) -> float:
        return max(0.0, 100.0 - (self.extract_feature_score(result, ["volatility_risk_score"]) or 100.0))

    _SCORE_HANDLERS = {
        "ML_SCORE": _score_ml,
        "ML_PROBABILITY": _score_ml_prob,
        "FINAL_SCORE": _score_final,
        "SIGNAL_SCORE": _score_signal,
        "CONFIDENCE": _score_confidence,
        "RISK_REWARD": _score_risk_reward,
        "LIQUIDITY": _score_liquidity,
        "VOLUME_ACTIVITY": _score_volume_activity,
        "MOMENTUM": _score_momentum,
        "TREND": _score_trend,
        "LOW_COST": _score_low_cost,
        "LOW_VOLATILITY": _score_low_volatility,
    }


    def _score_ml(self, result: SymbolScanResult) -> float:
        if not result.signal: return 0.0
        return float(result.signal.metadata.get("ml_prediction_score", 0.0))

    def _score_ml_prob(self, result: SymbolScanResult) -> float:
        if not result.signal: return 0.0
        val = result.signal.metadata.get("ml_probability_positive")
        return float(val) if val is not None else 0.0

    def _score_final(self, result: SymbolScanResult) -> float:
        if result.risk_decision and getattr(result.risk_decision, "final_score", None) is not None:
            return result.risk_decision.final_score
        if result.signal and getattr(result.signal, "score", None) is not None:
            return result.signal.score
        return 0.0

    def _score_signal(self, result: SymbolScanResult) -> float:
        if result.signal and getattr(result.signal, "score", None) is not None:
            return result.signal.score
        return 0.0

    def _score_confidence(self, result: SymbolScanResult) -> float:
        if result.signal and getattr(result.signal, "confidence", None) is not None:
            return result.signal.confidence
        return 0.0

    def _score_risk_reward(self, result: SymbolScanResult) -> float:
        if result.risk_decision and getattr(result.risk_decision, "stop_target", None):
            if getattr(result.risk_decision.stop_target, "risk_reward", None) is not None:
                return result.risk_decision.stop_target.risk_reward
        if result.signal and getattr(result.signal, "risk_reward", None) is not None:
            return result.signal.risk_reward
        return 0.0

    def _score_liquidity(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["liquidity_score", "volume_activity_score"]) or 0.0

    def _score_volume_activity(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["volume_activity_score"]) or 0.0

    def _score_momentum(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["momentum_strength_score", "momentum_direction_score"]) or 0.0

    def _score_trend(self, result: SymbolScanResult) -> float:
        return self.extract_feature_score(result, ["trend_strength_score"]) or 0.0

    def _score_low_cost(self, result: SymbolScanResult) -> float:
        return max(0.0, 100.0 - result.metadata.get("cost_bps", 100.0))

    def _score_low_volatility(self, result: SymbolScanResult) -> float:
        return max(0.0, 100.0 - (self.extract_feature_score(result, ["volatility_risk_score"]) or 100.0))

    _SCORE_HANDLERS = {
        ScanSortKey.ML_SCORE: _score_ml,
        ScanSortKey.ML_PROBABILITY: _score_ml_prob,
        ScanSortKey.FINAL_SCORE: _score_final,
        ScanSortKey.SIGNAL_SCORE: _score_signal,
        ScanSortKey.CONFIDENCE: _score_confidence,
        ScanSortKey.RISK_REWARD: _score_risk_reward,
        ScanSortKey.LIQUIDITY: _score_liquidity,
        ScanSortKey.VOLUME_ACTIVITY: _score_volume_activity,
        ScanSortKey.MOMENTUM: _score_momentum,
        ScanSortKey.TREND: _score_trend,
        ScanSortKey.LOW_COST: _score_low_cost,
        ScanSortKey.LOW_VOLATILITY: _score_low_volatility,
    }

    def calculate_rank_score(self, result: SymbolScanResult, sort_key: ScanSortKey) -> float:
        # Resolve string enum value to actual Enum if passed as string directly (from API for example)
        if isinstance(sort_key, str):
            for k in ScanSortKey:
                if k.value == sort_key:
                    sort_key = k
                    break

        handler = self._SCORE_HANDLERS.get(sort_key)
        if handler:
            return handler(self, result)
        return 0.0

    def extract_feature_score(self, result: SymbolScanResult, keys: List[str]) -> Optional[float]:
        if result.signal and result.signal.metadata and "features" in result.signal.metadata:
            feats = result.signal.metadata["features"]
            for k in keys:
                if k in feats and feats[k] is not None:
                    return float(feats[k])
        return None

def ranking_to_dataframe(rankings: List[ScanRankingItem]) -> 'pd.DataFrame':
    import pandas as pd
    if not rankings:
        return pd.DataFrame()
    data = [r.model_dump() for r in rankings]
    return pd.DataFrame(data)
