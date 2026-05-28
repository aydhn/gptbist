
from datetime import datetime
import uuid
from typing import List, Optional, Dict, Any
from bist_signal_bot.factors.models import FactorExposure, FactorScore, FactorStatus
from bist_signal_bot.factors.scoring import FactorScorer

class FactorExposureEngine:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.scorer = FactorScorer(settings)

    def exposure_for_symbol(self, symbol: str, as_of: Optional[datetime] = None) -> FactorExposure:
        from bist_signal_bot.factors.inputs import FactorInputBuilder
        builder = FactorInputBuilder(self.settings)
        snap = builder.build_input(symbol, as_of)
        scores = self.scorer.score_symbol(snap)

        agg = self.scorer.aggregate_scores(scores)
        dom = self.dominant_factors(scores)
        conc = self.factor_concentration_score(scores)

        return FactorExposure(
            exposure_id=str(uuid.uuid4()),
            object_type="SYMBOL",
            object_id=symbol,
            symbol=symbol,
            as_of=as_of or datetime.now(),
            factor_scores=scores,
            aggregate_factor_score=agg,
            dominant_factors=dom,
            factor_concentration_score=conc,
            status=FactorStatus.POSITIVE if agg and agg > 50 else FactorStatus.NEUTRAL
        )

    def exposure_for_signal(self, signal_payload: Dict[str, Any]) -> FactorExposure:
        return self.exposure_for_symbol(signal_payload.get("symbol", "UNKNOWN"))

    def exposure_for_strategy(self, strategy_name: str, symbols: Optional[List[str]] = None) -> FactorExposure:
        return FactorExposure(
            exposure_id=str(uuid.uuid4()),
            object_type="STRATEGY",
            object_id=strategy_name,
            strategy_name=strategy_name
        )

    def exposure_for_portfolio(self, positions: List[Any], as_of: Optional[datetime] = None) -> FactorExposure:
        return FactorExposure(
            exposure_id=str(uuid.uuid4()),
            object_type="PORTFOLIO",
            object_id="portfolio_mock",
            aggregate_factor_score=60.0,
            dominant_factors=["MOMENTUM"]
        )

    def dominant_factors(self, scores: List[FactorScore], top_n: int = 3) -> List[str]:
        valid = [s for s in scores if s.score is not None]
        valid.sort(key=lambda x: x.score, reverse=True)
        return [s.factor_type.value for s in valid[:top_n]]

    def factor_concentration_score(self, scores: List[FactorScore]) -> Optional[float]:
        valid = [s.score for s in scores if s.score is not None]
        if not valid: return None
        return float(max(valid))  # simplified
