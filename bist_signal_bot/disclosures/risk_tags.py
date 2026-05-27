import re
import uuid
from typing import List
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.disclosures.models import (
    DisclosureRecord, DisclosureRiskTag, DisclosureRiskTagType, DisclosureSeverity, DisclosureSentiment
)

class DisclosureRiskTagger:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def tag(self, record: DisclosureRecord) -> List[DisclosureRiskTag]:
        tags = []
        tags.extend(self.tag_financial_risks(record))
        tags.extend(self.tag_legal_regulatory(record))
        tags.extend(self.tag_corporate_actions(record))
        tags.extend(self.tag_liquidity_debt(record))
        for t in tags: t.score = self.score_tag(t)
        return tags

    def tag_financial_risks(self, record: DisclosureRecord) -> List[DisclosureRiskTag]:
        tags = []
        text = (record.title + " " + record.body).lower()
        if re.search(r"zarar|düşüş|beklentinin altında", text):
            tags.append(DisclosureRiskTag(tag_id=str(uuid.uuid4()), disclosure_id=record.disclosure_id, tag_type=DisclosureRiskTagType.EARNINGS_VOLATILITY, severity=DisclosureSeverity.HIGH, sentiment=DisclosureSentiment.NEGATIVE, message="Earnings volatility detected", evidence_text="Keywords like zarar/düşüş detected in disclosure."))
        if re.search(r"kur farkı|maliyet baskısı", text):
            tags.append(DisclosureRiskTag(tag_id=str(uuid.uuid4()), disclosure_id=record.disclosure_id, tag_type=DisclosureRiskTagType.MARGIN_PRESSURE, severity=DisclosureSeverity.MEDIUM, sentiment=DisclosureSentiment.NEGATIVE, message="Margin pressure risk", evidence_text="Keywords related to FX or cost pressure detected."))
        return tags

    def tag_legal_regulatory(self, record: DisclosureRecord) -> List[DisclosureRiskTag]:
        tags = []
        text = (record.title + " " + record.body).lower()
        if re.search(r"dava|ceza|soruşturma|düzenleyici kurum", text):
            tags.append(DisclosureRiskTag(tag_id=str(uuid.uuid4()), disclosure_id=record.disclosure_id, tag_type=DisclosureRiskTagType.LEGAL_REGULATORY, severity=DisclosureSeverity.HIGH, sentiment=DisclosureSentiment.NEGATIVE, message="Legal or regulatory risk", evidence_text="Legal keywords detected in disclosure."))
        return tags

    def tag_corporate_actions(self, record: DisclosureRecord) -> List[DisclosureRiskTag]:
        tags = []
        text = (record.title + " " + record.body).lower()
        if re.search(r"bedelli|sermaye artırımı|pay ihracı", text):
            tags.append(DisclosureRiskTag(tag_id=str(uuid.uuid4()), disclosure_id=record.disclosure_id, tag_type=DisclosureRiskTagType.DILUTION_RISK, severity=DisclosureSeverity.MEDIUM, sentiment=DisclosureSentiment.NEGATIVE, message="Potential dilution risk due to capital increase", evidence_text="Capital increase keywords detected."))
        if re.search(r"istifa|yönetim kurulu|genel müdür", text):
            tags.append(DisclosureRiskTag(tag_id=str(uuid.uuid4()), disclosure_id=record.disclosure_id, tag_type=DisclosureRiskTagType.MANAGEMENT_RISK, severity=DisclosureSeverity.MEDIUM, sentiment=DisclosureSentiment.UNCLEAR, message="Management change or risk", evidence_text="Management change keywords detected."))
        return tags

    def tag_liquidity_debt(self, record: DisclosureRecord) -> List[DisclosureRiskTag]:
        tags = []
        text = (record.title + " " + record.body).lower()
        if re.search(r"borç|kredi|finansman|temerrüt|yapılandırma", text):
            tags.append(DisclosureRiskTag(tag_id=str(uuid.uuid4()), disclosure_id=record.disclosure_id, tag_type=DisclosureRiskTagType.LIQUIDITY_PRESSURE, severity=DisclosureSeverity.HIGH, sentiment=DisclosureSentiment.NEGATIVE, message="Liquidity or debt pressure", evidence_text="Debt or financing keywords detected."))
        return tags

    def score_tag(self, tag: DisclosureRiskTag) -> float | None:
        base_score = 0.0
        if tag.severity == DisclosureSeverity.CRITICAL: base_score = 100.0
        elif tag.severity == DisclosureSeverity.HIGH: base_score = 75.0
        elif tag.severity == DisclosureSeverity.MEDIUM: base_score = 50.0
        elif tag.severity == DisclosureSeverity.LOW: base_score = 25.0
        elif tag.severity == DisclosureSeverity.INFO: base_score = 10.0

        if tag.sentiment == DisclosureSentiment.POSITIVE: base_score *= 0.5
        return base_score