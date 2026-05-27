from typing import List, Optional, Dict, Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.valuation.models import ValuationMultiple, ValuationBand, PeerValuationComparison, ValuationStatus

class ValuationScorer:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.w_hist = getattr(self.settings, "VALUATION_SCORE_WEIGHT_HISTORICAL", 0.40)
        self.w_peer = getattr(self.settings, "VALUATION_SCORE_WEIGHT_PEER", 0.35)
        self.w_qual = getattr(self.settings, "VALUATION_SCORE_WEIGHT_QUALITY", 0.15)
        self.w_data = getattr(self.settings, "VALUATION_SCORE_WEIGHT_DATA_QUALITY", 0.10)

    def _status_to_score(self, status: ValuationStatus) -> float:
        mapping = {
            ValuationStatus.EXTREME_CHEAP: 0.0,
            ValuationStatus.CHEAP: 25.0,
            ValuationStatus.FAIR: 50.0,
            ValuationStatus.EXPENSIVE: 75.0,
            ValuationStatus.EXTREME_EXPENSIVE: 100.0,
            ValuationStatus.WATCH: 60.0
        }
        return mapping.get(status, 50.0)

    def score_historical_bands(self, bands: List[ValuationBand]) -> Optional[float]:
        valid = [b for b in bands if b.status not in (ValuationStatus.INSUFFICIENT_DATA, ValuationStatus.ERROR, ValuationStatus.UNKNOWN)]
        if not valid:
            return None
        scores = [self._status_to_score(b.status) for b in valid]
        return sum(scores) / len(scores)

    def score_peer_relative(self, peers: List[PeerValuationComparison]) -> Optional[float]:
        valid = [p for p in peers if p.status not in (ValuationStatus.INSUFFICIENT_DATA, ValuationStatus.ERROR, ValuationStatus.UNKNOWN)]
        if not valid:
            return None
        scores = [self._status_to_score(p.status) for p in valid]
        return sum(scores) / len(scores)

    def score_data_quality(self, warnings: List[str]) -> Optional[float]:
        # More warnings = lower quality score, but for valuation context
        # a high score means expensive. Wait, data quality is a confidence multiplier,
        # but to blend linearly 0-100: we can map bad data to pulling the score towards 50 (neutral).
        # We will return a penalty weight instead of a directional score.
        penalty = min(len(warnings) * 10.0, 50.0)
        return 100.0 - penalty # 100 means perfect data, 50 means terrible.

    def combine_scores(self, parts: Dict[str, Optional[float]]) -> Optional[float]:
        # parts: hist, peer, qual, data
        valid_parts = {k: v for k, v in parts.items() if v is not None}
        if "hist" not in valid_parts and "peer" not in valid_parts:
            return None

        total_weight = 0.0
        weighted_sum = 0.0

        if "hist" in valid_parts:
            weighted_sum += valid_parts["hist"] * self.w_hist
            total_weight += self.w_hist
        if "peer" in valid_parts:
            weighted_sum += valid_parts["peer"] * self.w_peer
            total_weight += self.w_peer

        base_score = weighted_sum / total_weight if total_weight > 0 else 50.0

        # Adjust for earnings quality (value trap logic)
        # If cheap (< 50) and quality is bad (< 40), push score up (less attractive)
        # If expensive (> 50) and quality is good (> 70), pull score down (more justifiable)
        if "qual" in valid_parts:
            qual = valid_parts["qual"]
            if base_score < 50 and qual < 40:
                base_score += (40 - qual) * 0.5 # Penalty for value trap
            elif base_score > 50 and qual > 70:
                base_score -= (qual - 70) * 0.5 # Premium justified

        # Data quality pulls extreme scores towards 50
        if "data" in valid_parts:
            data = valid_parts["data"] # 100 is good, 50 is bad
            pull_factor = (100.0 - data) / 100.0 # 0.0 to 0.5
            base_score = base_score * (1.0 - pull_factor) + 50.0 * pull_factor

        return max(0.0, min(100.0, base_score))

    def score_valuation(self, multiples: List[ValuationMultiple], bands: List[ValuationBand],
                        peers: List[PeerValuationComparison], earnings_quality: Optional[Dict] = None) -> Optional[float]:
        hist_score = self.score_historical_bands(bands)
        peer_score = self.score_peer_relative(peers)

        warnings = []
        for lst in [multiples, bands, peers]:
            for item in lst: warnings.extend(item.warnings)

        data_score = self.score_data_quality(list(set(warnings)))
        qual_score = earnings_quality.get("score") if earnings_quality else None

        parts = {
            "hist": hist_score,
            "peer": peer_score,
            "qual": qual_score,
            "data": data_score
        }

        return self.combine_scores(parts)
