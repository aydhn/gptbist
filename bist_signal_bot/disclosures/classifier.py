from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureType, DisclosureSentiment, DisclosureSeverity

class DisclosureClassifier:
    def classify(self, record: DisclosureRecord) -> DisclosureRecord:
        if record.disclosure_type == DisclosureType.UNKNOWN:
            record.disclosure_type = self.classify_type(record.title, record.body)
        if record.sentiment == DisclosureSentiment.UNKNOWN:
            record.sentiment = self.classify_sentiment(record.title, record.body)
        if record.severity == DisclosureSeverity.UNKNOWN:
            record.severity = self.classify_severity(record)
        record.confidence = self.confidence_for_classification(record)
        return record

    def classify_type(self, title: str, body: str) -> DisclosureType:
        text = (title + " " + body).lower()
        if "bilanço" in text or "finansal rapor" in text:
            return DisclosureType.FINANCIAL_STATEMENT
        if "temettü" in text or "kar payı" in text:
            return DisclosureType.DIVIDEND
        if "dava" in text or "mahkeme" in text:
            return DisclosureType.LEGAL_CASE
        if "ihale" in text:
            return DisclosureType.CONTRACT_TENDER
        if "sermaye" in text and "artırım" in text:
            return DisclosureType.CAPITAL_INCREASE
        return DisclosureType.MATERIAL_EVENT

    def classify_sentiment(self, title: str, body: str) -> DisclosureSentiment:
        text = (title + " " + body).lower()
        positive_keywords = ["kazanıldı", "arttı", "büyüme", "kâr", "olumlu"]
        negative_keywords = ["ceza", "iptal", "düştü", "zarar", "dava", "olumsuz"]

        pos_count = sum(1 for k in positive_keywords if k in text)
        neg_count = sum(1 for k in negative_keywords if k in text)

        if pos_count > neg_count:
            return DisclosureSentiment.POSITIVE
        elif neg_count > pos_count:
            return DisclosureSentiment.NEGATIVE
        elif pos_count > 0 and neg_count > 0:
            return DisclosureSentiment.MIXED
        return DisclosureSentiment.NEUTRAL

    def classify_severity(self, record: DisclosureRecord) -> DisclosureSeverity:
        if record.disclosure_type in [DisclosureType.LEGAL_CASE, DisclosureType.REGULATORY_ACTION]:
            return DisclosureSeverity.HIGH
        return DisclosureSeverity.MEDIUM

    def confidence_for_classification(self, record: DisclosureRecord) -> float:
        return 80.0
