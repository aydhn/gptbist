import uuid
from typing import List
from bist_signal_bot.disclosures.models import (
    DisclosureRecord,
    DisclosureRiskTag,
    DisclosureRiskTagType,
    DisclosureSeverity,
    DisclosureSentiment
)

class DisclosureRiskTagger:
    def __init__(self, settings=None):
        self.settings = settings

        self.debt_keywords = ["borç", "kredi", "finansman", "temerrüt", "yapılandırma"]
        self.legal_keywords = ["dava", "ceza", "soruşturma", "düzenleyici kurum", "spk", "rekabet kurulu"]
        self.dilution_keywords = ["sermaye artırımı", "bedelli", "pay ihracı"]
        self.liquidity_keywords = ["nakit sıkıntısı", "likidite", "ödeme zorluğu"]

    def tag(self, record: DisclosureRecord) -> List[DisclosureRiskTag]:
        tags = []
        tags.extend(self.tag_financial_risks(record))
        tags.extend(self.tag_legal_regulatory(record))
        tags.extend(self.tag_corporate_actions(record))
        tags.extend(self.tag_liquidity_debt(record))
        return tags

    def tag_financial_risks(self, record: DisclosureRecord) -> List[DisclosureRiskTag]:
        # Dummy logic
        return []

    def tag_legal_regulatory(self, record: DisclosureRecord) -> List[DisclosureRiskTag]:
        tags = []
        text = f"{record.title} {record.body}".lower()
        if any(k in text for k in self.legal_keywords):
            tag = DisclosureRiskTag(
                tag_id=f"tag_{uuid.uuid4().hex[:8]}",
                disclosure_id=record.disclosure_id,
                tag_type=DisclosureRiskTagType.LEGAL_REGULATORY,
                severity=DisclosureSeverity.HIGH,
                sentiment=DisclosureSentiment.NEGATIVE,
                message="Hukuki veya düzenleyici kurum riski tespit edildi.",
                evidence_text="Keywords matched in disclosure text."
            )
            tag.score = self.score_tag(tag)
            tags.append(tag)
        return tags

    def tag_corporate_actions(self, record: DisclosureRecord) -> List[DisclosureRiskTag]:
        tags = []
        text = f"{record.title} {record.body}".lower()
        if any(k in text for k in self.dilution_keywords):
            tag = DisclosureRiskTag(
                tag_id=f"tag_{uuid.uuid4().hex[:8]}",
                disclosure_id=record.disclosure_id,
                tag_type=DisclosureRiskTagType.DILUTION_RISK,
                severity=DisclosureSeverity.MEDIUM,
                sentiment=DisclosureSentiment.NEGATIVE,
                message="Sermaye artırımı/sulandırma riski."
            )
            tag.score = self.score_tag(tag)
            tags.append(tag)
        return tags

    def tag_liquidity_debt(self, record: DisclosureRecord) -> List[DisclosureRiskTag]:
        tags = []
        text = f"{record.title} {record.body}".lower()
        if any(k in text for k in self.debt_keywords):
            tag = DisclosureRiskTag(
                tag_id=f"tag_{uuid.uuid4().hex[:8]}",
                disclosure_id=record.disclosure_id,
                tag_type=DisclosureRiskTagType.HIGH_LEVERAGE,
                severity=DisclosureSeverity.MEDIUM,
                sentiment=DisclosureSentiment.NEGATIVE,
                message="Borçlanma veya finansman vurgusu."
            )
            tag.score = self.score_tag(tag)
            tags.append(tag)

        if any(k in text for k in self.liquidity_keywords):
            tag = DisclosureRiskTag(
                tag_id=f"tag_{uuid.uuid4().hex[:8]}",
                disclosure_id=record.disclosure_id,
                tag_type=DisclosureRiskTagType.LIQUIDITY_PRESSURE,
                severity=DisclosureSeverity.HIGH,
                sentiment=DisclosureSentiment.NEGATIVE,
                message="Likidite baskısı veya ödeme zorluğu uyarısı."
            )
            tag.score = self.score_tag(tag)
            tags.append(tag)

        return tags

    def score_tag(self, tag: DisclosureRiskTag) -> float | None:
        if tag.sentiment == DisclosureSentiment.POSITIVE:
            return 0.0
        if tag.severity == DisclosureSeverity.CRITICAL:
            return 90.0
        elif tag.severity == DisclosureSeverity.HIGH:
            return 70.0
        elif tag.severity == DisclosureSeverity.MEDIUM:
            return 40.0
        elif tag.severity == DisclosureSeverity.LOW:
            return 10.0
        return 0.0
