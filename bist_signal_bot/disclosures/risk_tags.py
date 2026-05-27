from typing import List
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureRiskTag, DisclosureRiskTagType, DisclosureSeverity, DisclosureSentiment

class DisclosureRiskTagger:
    def tag(self, record: DisclosureRecord) -> List[DisclosureRiskTag]:
        tags = []
        tags.extend(self.tag_financial_risks(record))
        tags.extend(self.tag_legal_regulatory(record))
        tags.extend(self.tag_corporate_actions(record))
        tags.extend(self.tag_liquidity_debt(record))
        return tags

    def tag_financial_risks(self, record: DisclosureRecord) -> List[DisclosureRiskTag]:
        return []

    def tag_legal_regulatory(self, record: DisclosureRecord) -> List[DisclosureRiskTag]:
        tags = []
        text = (record.title + " " + record.body).lower()
        if "ceza" in text or "dava" in text or "soruşturma" in text:
            tags.append(DisclosureRiskTag(
                tag_id="tag_legal",
                disclosure_id=record.disclosure_id,
                tag_type=DisclosureRiskTagType.LEGAL_REGULATORY,
                severity=DisclosureSeverity.HIGH,
                sentiment=DisclosureSentiment.NEGATIVE,
                message="Legal or regulatory risk detected.",
                score=self.score_tag(DisclosureRiskTagType.LEGAL_REGULATORY)
            ))
        return tags

    def tag_corporate_actions(self, record: DisclosureRecord) -> List[DisclosureRiskTag]:
        tags = []
        text = (record.title + " " + record.body).lower()
        if "sermaye artırımı" in text or "bedelli" in text or "pay ihracı" in text:
            tags.append(DisclosureRiskTag(
                tag_id="tag_dilution",
                disclosure_id=record.disclosure_id,
                tag_type=DisclosureRiskTagType.DILUTION_RISK,
                severity=DisclosureSeverity.MEDIUM,
                sentiment=DisclosureSentiment.NEGATIVE,
                message="Dilution risk detected due to capital increase.",
                score=self.score_tag(DisclosureRiskTagType.DILUTION_RISK)
            ))
        return tags

    def tag_liquidity_debt(self, record: DisclosureRecord) -> List[DisclosureRiskTag]:
        tags = []
        text = (record.title + " " + record.body).lower()
        if "borç" in text or "kredi" in text or "temerrüt" in text:
            tags.append(DisclosureRiskTag(
                tag_id="tag_debt",
                disclosure_id=record.disclosure_id,
                tag_type=DisclosureRiskTagType.LIQUIDITY_PRESSURE,
                severity=DisclosureSeverity.HIGH,
                sentiment=DisclosureSentiment.NEGATIVE,
                message="Liquidity pressure or debt risk detected.",
                score=self.score_tag(DisclosureRiskTagType.LIQUIDITY_PRESSURE)
            ))
        return tags

    def score_tag(self, tag_type: DisclosureRiskTagType | DisclosureRiskTag) -> float | None:
        if isinstance(tag_type, DisclosureRiskTag):
            tag_type = tag_type.tag_type
        if tag_type in [DisclosureRiskTagType.LEGAL_REGULATORY, DisclosureRiskTagType.LIQUIDITY_PRESSURE]:
            return 80.0
        return 50.0
