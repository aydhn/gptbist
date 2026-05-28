
from datetime import datetime
import uuid
import numpy as np
from typing import List, Optional, Dict
from bist_signal_bot.factors.models import FactorScore, FactorInputSnapshot, FactorType, FactorStatus, FactorExposureDirection
from bist_signal_bot.factors.library import FactorLibrary

class FactorScorer:
    def __init__(self, settings=None):
        self.settings = settings
        self.library = FactorLibrary(settings)

    def score_symbol(self, input_snap: FactorInputSnapshot, universe_inputs: Optional[List[FactorInputSnapshot]] = None) -> List[FactorScore]:
        scores = []
        for ftype in self.library.supported_factors():
            score = self.score_factor(input_snap, ftype, universe_inputs)
            scores.append(score)
        return scores

    def score_factor(self, input_snap: FactorInputSnapshot, factor_type: FactorType, universe_inputs: Optional[List[FactorInputSnapshot]] = None) -> FactorScore:
        val = None
        if factor_type == FactorType.MOMENTUM:
            val = input_snap.price_return_20d_pct
        elif factor_type == FactorType.VALUE:
            val = input_snap.valuation_score
        elif factor_type == FactorType.LEVERAGE:
            val = input_snap.debt_to_equity

        higher_is_better = self.library.direction(factor_type) == "HIGHER_IS_BETTER"

        # mock universe parsing
        peers = [5.0, 10.0, 15.0] if val is not None else []

        pct_rank = self.percentile_score(val, peers, higher_is_better)
        z = self.z_score(val, peers)

        # Determine 0-100 score
        final_score = pct_rank if pct_rank is not None else (50.0 if val is not None else None)

        status = self.classify_score(final_score)

        return FactorScore(
            score_id=str(uuid.uuid4()),
            symbol=input_snap.symbol,
            factor_type=factor_type,
            as_of=input_snap.as_of,
            raw_value=val,
            percentile_rank=pct_rank,
            z_score=z,
            score=final_score,
            status=status,
            direction=FactorExposureDirection.LONG_EXPOSURE if (final_score or 0) > 50 else FactorExposureDirection.SHORT_EXPOSURE
        )

    def percentile_score(self, value: Optional[float], peer_values: List[float], higher_is_better: bool = True) -> Optional[float]:
        if value is None or not peer_values:
            return None
        arr = np.array(peer_values)
        if higher_is_better:
            pct = np.sum(arr <= value) / len(arr) * 100
        else:
            pct = np.sum(arr >= value) / len(arr) * 100
        return float(pct)

    def z_score(self, value: Optional[float], peer_values: List[float]) -> Optional[float]:
        if value is None or not peer_values or len(peer_values) < 2:
            return None
        mean = np.mean(peer_values)
        std = np.std(peer_values)
        if std == 0:
            return 0.0
        return float((value - mean) / std)

    def classify_score(self, score: Optional[float]) -> FactorStatus:
        if score is None:
            return FactorStatus.INSUFFICIENT_DATA
        if score >= 75.0:
            return FactorStatus.STRONG
        if score >= 60.0:
            return FactorStatus.POSITIVE
        if score <= 25.0:
            return FactorStatus.WEAK
        if score <= 40.0:
            return FactorStatus.NEGATIVE
        return FactorStatus.NEUTRAL

    def aggregate_scores(self, scores: List[FactorScore], weights: Optional[Dict[FactorType, float]] = None) -> Optional[float]:
        if not scores:
            return None
        weights = weights or self.library.default_weights()
        total_w = 0.0
        total_s = 0.0
        for s in scores:
            if s.score is not None and s.factor_type in weights:
                w = weights[s.factor_type]
                total_w += w
                total_s += s.score * w
        if total_w == 0:
            return None
        return total_s / total_w
