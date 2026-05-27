import uuid
import re
from typing import List, Dict, Optional
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.disclosures.models import (
    DisclosureRecord, DisclosureImpactAssessment, DisclosureRiskTag, DisclosureRiskTagType, DisclosureSeverity, DisclosureSentiment
)

class DisclosureImpactAssessor:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def assess(self, record: DisclosureRecord, risk_tags: List[DisclosureRiskTag] | None = None) -> DisclosureImpactAssessment:
        risk_tags = risk_tags or []
        narrative_score = self.narrative_risk_score(record, risk_tags)
        conf_adj = self.confidence_adjustment(record, narrative_score)
        event_delta = self.event_risk_delta(record, narrative_score)
        liq_vol_deltas = self.liquidity_volatility_deltas(record, risk_tags)

        assessment = DisclosureImpactAssessment(
            assessment_id=str(uuid.uuid4()), disclosure_id=record.disclosure_id, symbols=record.symbols,
            disclosure_type=record.disclosure_type, sentiment=record.sentiment, severity=record.severity,
            narrative_risk_score=narrative_score, event_risk_score_delta=event_delta, confidence_adjustment=conf_adj,
            liquidity_risk_delta=liq_vol_deltas.get('liquidity'), volatility_risk_delta=liq_vol_deltas.get('volatility'), risk_tags=risk_tags
        )

        if narrative_score is not None:
            if narrative_score >= getattr(self.settings, 'DISCLOSURE_RISK_SCORE_HIGH', 80.0): assessment.recommended_decision = "BLOCK"
            elif narrative_score >= getattr(self.settings, 'DISCLOSURE_RISK_SCORE_REVIEW', 65.0): assessment.recommended_decision = "REQUIRE_REVIEW"
            elif narrative_score >= getattr(self.settings, 'DISCLOSURE_RISK_SCORE_WARN', 40.0): assessment.recommended_decision = "WARN"

        if any(t.tag_type == DisclosureRiskTagType.POSITIVE_CATALYST_PLACEHOLDER for t in risk_tags):
            assessment.warnings.append("Positive catalyst detected, but it does not predict price direction.")

        return assessment

    def narrative_risk_score(self, record: DisclosureRecord, risk_tags: List[DisclosureRiskTag]) -> Optional[float]:
        score = 0.0
        if record.severity == DisclosureSeverity.CRITICAL: score += 60.0
        elif record.severity == DisclosureSeverity.HIGH: score += 40.0
        elif record.severity == DisclosureSeverity.MEDIUM: score += 20.0

        for tag in risk_tags:
            if tag.score: score += tag.score

        if record.sentiment == DisclosureSentiment.NEGATIVE: score *= 1.5
        elif record.sentiment == DisclosureSentiment.POSITIVE: score *= 0.5

        if re.search(r'ihale|anlaşma|yeni proje', (record.title + " " + record.body).lower()):
            risk_tags.append(DisclosureRiskTag(tag_id=str(uuid.uuid4()), disclosure_id=record.disclosure_id, tag_type=DisclosureRiskTagType.POSITIVE_CATALYST_PLACEHOLDER, severity=DisclosureSeverity.INFO, sentiment=DisclosureSentiment.POSITIVE, message="Positive catalyst placeholder", evidence_text="Positive project/tender keywords found."))

        return min(100.0, score)

    def confidence_adjustment(self, record: DisclosureRecord, score: Optional[float]) -> Optional[float]:
        if score is None: return 0.0
        if score >= getattr(self.settings, 'DISCLOSURE_RISK_SCORE_HIGH', 80.0): return getattr(self.settings, 'DISCLOSURE_CONFIDENCE_ADJUSTMENT_HIGH', -12.0)
        elif score >= getattr(self.settings, 'DISCLOSURE_RISK_SCORE_REVIEW', 65.0): return getattr(self.settings, 'DISCLOSURE_CONFIDENCE_ADJUSTMENT_REVIEW', -7.0)
        elif score >= getattr(self.settings, 'DISCLOSURE_RISK_SCORE_WARN', 40.0): return getattr(self.settings, 'DISCLOSURE_CONFIDENCE_ADJUSTMENT_WARN', -3.0)
        return 0.0

    def event_risk_delta(self, record: DisclosureRecord, score: Optional[float]) -> Optional[float]:
        if score is None: return 0.0
        return score * 0.1

    def liquidity_volatility_deltas(self, record: DisclosureRecord, risk_tags: List[DisclosureRiskTag]) -> Dict[str, Optional[float]]:
        deltas = {'liquidity': 0.0, 'volatility': 0.0}
        for tag in risk_tags:
            if tag.tag_type == DisclosureRiskTagType.LIQUIDITY_PRESSURE: deltas['liquidity'] = -20.0
            if tag.tag_type == DisclosureRiskTagType.EARNINGS_VOLATILITY: deltas['volatility'] = 30.0
        return deltas