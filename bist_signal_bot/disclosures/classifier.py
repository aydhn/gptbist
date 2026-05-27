from bist_signal_bot.disclosures.models import (
    DisclosureRecord,
    DisclosureType,
    DisclosureSentiment,
    DisclosureSeverity
)

class DisclosureClassifier:
    def __init__(self, settings=None):
        self.settings = settings

        # Simple deterministic keyword dictionaries
        self.type_keywords = {
            DisclosureType.FINANCIAL_STATEMENT: ["finansal tablo", "bilanço", "gelir tablosu", "mali tablo"],
            DisclosureType.DIVIDEND: ["temettü", "kâr payı", "kar payı"],
            DisclosureType.CAPITAL_INCREASE: ["sermaye artırımı", "bedelli", "bedelsiz"],
            DisclosureType.LEGAL_CASE: ["dava", "mahkeme", "hukuki süreç", "soruşturma"],
            DisclosureType.CONTRACT_TENDER: ["ihale", "sözleşme", "anlaşma", "sipariş"],
            DisclosureType.MANAGEMENT_CHANGE: ["istifa", "yönetim kurulu", "atama", "görevden ayrılma"],
        }

        self.sentiment_positive = ["artış", "olumlu", "büyüme", "kâr", "kazanç", "ihale kazandı"]
        self.sentiment_negative = ["düşüş", "olumsuz", "zarar", "iptal", "ceza", "dava", "istifa", "azalma"]

    def classify(self, record: DisclosureRecord) -> DisclosureRecord:
        if record.disclosure_type == DisclosureType.UNKNOWN:
            record.disclosure_type = self.classify_type(record.title, record.body)

        if record.sentiment == DisclosureSentiment.UNKNOWN:
            record.sentiment = self.classify_sentiment(record.title, record.body)

        if record.severity == DisclosureSeverity.UNKNOWN:
            record.severity = self.classify_severity(record)

        record.confidence = self.confidence_for_classification(record)

        if record.disclosure_type == DisclosureType.UNKNOWN:
            if "unknown_type" not in record.warnings:
                record.warnings.append("unknown_type")

        return record

    def classify_type(self, title: str, body: str) -> DisclosureType:
        text = f"{title} {body}".lower()

        # Check title first (higher weight implicitly)
        title_lower = title.lower()
        for dtype, keywords in self.type_keywords.items():
            if any(k in title_lower for k in keywords):
                return dtype

        # Fallback to body
        for dtype, keywords in self.type_keywords.items():
            if any(k in text for k in keywords):
                return dtype

        return DisclosureType.MATERIAL_EVENT # Default to material event if unsure, or UNKNOWN

    def classify_sentiment(self, title: str, body: str) -> DisclosureSentiment:
        text = f"{title} {body}".lower()

        pos_count = sum(1 for k in self.sentiment_positive if k in text)
        neg_count = sum(1 for k in self.sentiment_negative if k in text)

        if pos_count > neg_count * 2:
            return DisclosureSentiment.POSITIVE
        elif neg_count > pos_count * 2:
            return DisclosureSentiment.NEGATIVE
        elif pos_count > 0 and neg_count > 0:
            return DisclosureSentiment.MIXED
        elif pos_count == 0 and neg_count == 0:
            return DisclosureSentiment.NEUTRAL
        else:
            return DisclosureSentiment.UNCLEAR

    def classify_severity(self, record: DisclosureRecord) -> DisclosureSeverity:
        # Simple heuristic based on type and keywords
        text = f"{record.title} {record.body}".lower()

        critical_keywords = ["iflas", "temerrüt", "faaliyetlerin durdurulması", "gözaltı", "büyük çaplı"]
        high_keywords = ["dava açıldı", "ceza", "büyük", "önemli", "istifa", "zarar"]

        if any(k in text for k in critical_keywords):
            return DisclosureSeverity.CRITICAL

        if record.disclosure_type in [DisclosureType.FINANCIAL_STATEMENT, DisclosureType.CAPITAL_INCREASE, DisclosureType.DIVIDEND]:
            return DisclosureSeverity.HIGH

        if any(k in text for k in high_keywords):
            return DisclosureSeverity.HIGH

        return DisclosureSeverity.MEDIUM

    def confidence_for_classification(self, record: DisclosureRecord) -> float:
        # Deterministic dummy confidence based on how much was classified
        conf = 50.0
        if record.disclosure_type != DisclosureType.UNKNOWN:
            conf += 20.0
        if record.sentiment not in [DisclosureSentiment.UNKNOWN, DisclosureSentiment.UNCLEAR]:
            conf += 15.0
        if record.symbols:
            conf += 15.0
        return min(100.0, conf)
