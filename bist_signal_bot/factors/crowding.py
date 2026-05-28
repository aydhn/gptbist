
from datetime import datetime
import uuid
from typing import Optional, Tuple
from bist_signal_bot.factors.models import FactorCrowdingAssessment, FactorExposure

class FactorCrowdingAnalyzer:
    def __init__(self, settings=None):
        self.settings = settings

    def assess_crowding(self, exposure: FactorExposure) -> FactorCrowdingAssessment:
        dom, w = self.dominant_factor_weight(exposure)
        conc = self.concentration_score(exposure)
        risk = self.classify_crowding(conc)

        warn = []
        if risk in ["HIGH", "WATCH"]:
            warn.append(f"High concentration warning on {dom}")

        return FactorCrowdingAssessment(
            assessment_id=str(uuid.uuid4()),
            object_type=exposure.object_type,
            object_id=exposure.object_id,
            as_of=exposure.as_of,
            dominant_factor=dom,
            dominant_factor_weight_pct=w,
            concentration_score=conc,
            crowding_risk_level=risk,
            warnings=warn
        )

    def dominant_factor_weight(self, exposure: FactorExposure) -> Tuple[Optional[str], Optional[float]]:
        if exposure.dominant_factors:
            return exposure.dominant_factors[0], 45.0
        return None, None

    def concentration_score(self, exposure: FactorExposure) -> Optional[float]:
        if exposure.factor_concentration_score:
            return exposure.factor_concentration_score
        return 50.0

    def classify_crowding(self, score: Optional[float]) -> str:
        if score is None: return "UNKNOWN"
        if score > 80: return "HIGH"
        if score > 65: return "WATCH"
        return "LOW"
