from typing import List, Dict, Optional
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureRiskTag, DisclosureImpactAssessment, DisclosureSentiment, DisclosureSeverity

class DisclosureImpactAssessor:
    def assess(self, record: DisclosureRecord, risk_tags: Optional[List[DisclosureRiskTag]] = None) -> DisclosureImpactAssessment:
        if risk_tags is None:
            risk_tags = []

        score = self.narrative_risk_score(record, risk_tags)

        return DisclosureImpactAssessment(
            assessment_id=f"ass_{record.disclosure_id}",
            disclosure_id=record.disclosure_id,
            symbols=record.symbols,
            disclosure_type=record.disclosure_type,
            sentiment=record.sentiment,
            severity=record.severity,
            narrative_risk_score=score,
            event_risk_score_delta=self.event_risk_delta(record, score),
            confidence_adjustment=self.confidence_adjustment(record, score),
            liquidity_risk_delta=self.liquidity_volatility_deltas(record, risk_tags).get("liquidity", 0.0),
            volatility_risk_delta=self.liquidity_volatility_deltas(record, risk_tags).get("volatility", 0.0),
            recommended_decision="REVIEW" if score and score > 50 else "NONE",
            risk_tags=risk_tags
        )

    def narrative_risk_score(self, record: DisclosureRecord, risk_tags: List[DisclosureRiskTag]) -> Optional[float]:
        score = 0.0
        if record.sentiment == DisclosureSentiment.NEGATIVE:
            score += 20.0
        if record.severity == DisclosureSeverity.HIGH:
            score += 20.0
        elif record.severity == DisclosureSeverity.CRITICAL:
            score += 40.0

        for tag in risk_tags:
            if tag.score:
                score += tag.score * 0.2

        return min(100.0, score)

    def confidence_adjustment(self, record: DisclosureRecord, score: Optional[float]) -> Optional[float]:
        if score is None:
            return 0.0
        if score > 80:
            return -12.0
        if score > 65:
            return -7.0
        if score > 40:
            return -3.0
        return 0.0

    def event_risk_delta(self, record: DisclosureRecord, score: Optional[float]) -> Optional[float]:
        if score is None:
            return 0.0
        return score * 0.1

    def liquidity_volatility_deltas(self, record: DisclosureRecord, risk_tags: List[DisclosureRiskTag]) -> Dict[str, Optional[float]]:
        return {"liquidity": 0.0, "volatility": 0.0}
