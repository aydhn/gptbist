import uuid
from typing import List, Dict, Optional
from bist_signal_bot.disclosures.models import (
    DisclosureRecord,
    DisclosureRiskTag,
    DisclosureImpactAssessment,
    DisclosureSentiment,
    DisclosureSeverity
)

class DisclosureImpactAssessor:
    def __init__(self, settings=None):
        self.settings = settings

    def assess(self, record: DisclosureRecord, risk_tags: Optional[List[DisclosureRiskTag]] = None) -> DisclosureImpactAssessment:
        if risk_tags is None:
            risk_tags = []

        assessment = DisclosureImpactAssessment(
            assessment_id=f"ias_{uuid.uuid4().hex[:8]}",
            disclosure_id=record.disclosure_id,
            symbols=record.symbols.copy(),
            disclosure_type=record.disclosure_type,
            sentiment=record.sentiment,
            severity=record.severity,
            risk_tags=risk_tags
        )

        assessment.narrative_risk_score = self.narrative_risk_score(record, risk_tags)
        assessment.confidence_adjustment = self.confidence_adjustment(record, assessment.narrative_risk_score)
        assessment.event_risk_score_delta = self.event_risk_delta(record, assessment.narrative_risk_score)

        deltas = self.liquidity_volatility_deltas(record, risk_tags)
        assessment.liquidity_risk_delta = deltas.get("liquidity")
        assessment.volatility_risk_delta = deltas.get("volatility")

        if assessment.narrative_risk_score and assessment.narrative_risk_score > 70:
            assessment.recommended_decision = "REQUIRE_REVIEW"

        return assessment

    def narrative_risk_score(self, record: DisclosureRecord, risk_tags: List[DisclosureRiskTag]) -> Optional[float]:
        base_score = 0.0

        if record.severity == DisclosureSeverity.CRITICAL:
            base_score = 80.0
        elif record.severity == DisclosureSeverity.HIGH:
            base_score = 50.0
        elif record.severity == DisclosureSeverity.MEDIUM:
            base_score = 25.0

        if record.sentiment == DisclosureSentiment.NEGATIVE:
            base_score += 20.0
        elif record.sentiment == DisclosureSentiment.POSITIVE:
            base_score = max(0.0, base_score - 20.0)

        tag_scores = [t.score for t in risk_tags if t.score is not None]
        if tag_scores:
            # Add weighted tag score
            base_score += max(tag_scores) * 0.5

        return min(100.0, max(0.0, base_score))

    def confidence_adjustment(self, record: DisclosureRecord, score: Optional[float]) -> Optional[float]:
        if score is None:
            return 0.0
        if score > 80:
            return -15.0
        elif score > 60:
            return -10.0
        elif score > 40:
            return -5.0
        return 0.0

    def event_risk_delta(self, record: DisclosureRecord, score: Optional[float]) -> Optional[float]:
        if score is None:
            return 0.0
        return score * 0.5

    def liquidity_volatility_deltas(self, record: DisclosureRecord, risk_tags: List[DisclosureRiskTag]) -> Dict[str, Optional[float]]:
        deltas = {"liquidity": 0.0, "volatility": 0.0}

        tag_types = [t.tag_type.value for t in risk_tags]
        if "LIQUIDITY_PRESSURE" in tag_types:
            deltas["liquidity"] = 30.0

        if record.disclosure_type.value in ["FINANCIAL_STATEMENT", "LEGAL_CASE", "MATERIAL_EVENT"]:
            deltas["volatility"] = 20.0

        if record.severity in [DisclosureSeverity.HIGH, DisclosureSeverity.CRITICAL]:
            deltas["volatility"] += 15.0

        return deltas
