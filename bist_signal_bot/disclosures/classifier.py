import re
from typing import List
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.disclosures.models import (
    DisclosureRecord, DisclosureType, DisclosureSentiment, DisclosureSeverity, DisclosureProcessingStatus
)

class DisclosureClassifier:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.type_rules = {
            DisclosureType.FINANCIAL_STATEMENT: [r"bilanço", r"finansal tablo", r"gelir tablosu", r"faaliyet raporu"],
            DisclosureType.DIVIDEND: [r"temettü", r"kâr payı"],
            DisclosureType.CAPITAL_INCREASE: [r"sermaye artırım", r"bedelli", r"bedelsiz"],
            DisclosureType.CAPITAL_DECREASE: [r"sermaye azaltım"],
            DisclosureType.SHARE_BUYBACK: [r"pay alım", r"geri alım"],
            DisclosureType.CONTRACT_TENDER: [r"ihale", r"sözleşme", r"iş ilişkisi", r"anlaşma"],
            DisclosureType.INVESTMENT_PROJECT: [r"yatırım", r"kapasite artış", r"yeni tesis"],
            DisclosureType.DEBT_FINANCING: [r"kredi", r"borçlanma", r"tahvil", r"finansman"],
            DisclosureType.LEGAL_CASE: [r"dava", r"mahkeme", r"ceza", r"soruşturma"],
            DisclosureType.REGULATORY_ACTION: [r"spk", r"düzenleyici kurum", r"rekabet kurumu"],
            DisclosureType.MANAGEMENT_CHANGE: [r"istifa", r"atama", r"yönetim kurulu", r"genel müdür"],
            DisclosureType.MATERIAL_EVENT: [r"özel durum", r"maddi duran varlık"],
        }
        self.positive_keywords = [r"kâr", r"büyüme", r"artış", r"olumlu", r"temettü", r"ihaleyi kazandı", r"anlaşma sağlandı", r"yeni iş ilişkisi"]
        self.negative_keywords = [r"zarar", r"düşüş", r"olumsuz", r"ceza", r"dava", r"istifa", r"iptal", r"zararına", r"ret"]

    def classify(self, record: DisclosureRecord) -> DisclosureRecord:
        if record.disclosure_type == DisclosureType.UNKNOWN:
            record.disclosure_type = self.classify_type(record.title, record.body)
        if record.sentiment == DisclosureSentiment.UNKNOWN:
            record.sentiment = self.classify_sentiment(record.title, record.body)
        if record.severity == DisclosureSeverity.UNKNOWN:
            record.severity = self.classify_severity(record)

        record.confidence = self.confidence_for_classification(record)
        record.status = DisclosureProcessingStatus.CLASSIFIED

        if record.disclosure_type == DisclosureType.UNKNOWN:
            record.warnings.append("Classification resulted in UNKNOWN type.")
        return record

    def classify_type(self, title: str, body: str) -> DisclosureType:
        text = (title + " " + body).lower()
        for d_type, patterns in self.type_rules.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return d_type
        return DisclosureType.UNKNOWN

    def classify_sentiment(self, title: str, body: str) -> DisclosureSentiment:
        text = (title + " " + body).lower()
        pos_count = sum(1 for p in self.positive_keywords if re.search(p, text))
        neg_count = sum(1 for p in self.negative_keywords if re.search(p, text))

        if pos_count > 0 and neg_count == 0: return DisclosureSentiment.POSITIVE
        elif neg_count > 0 and pos_count == 0: return DisclosureSentiment.NEGATIVE
        elif pos_count > 0 and neg_count > 0: return DisclosureSentiment.MIXED
        else: return DisclosureSentiment.NEUTRAL

    def classify_severity(self, record: DisclosureRecord) -> DisclosureSeverity:
        d_type = record.disclosure_type
        if d_type in [DisclosureType.LEGAL_CASE, DisclosureType.REGULATORY_ACTION]: return DisclosureSeverity.HIGH
        elif d_type in [DisclosureType.FINANCIAL_STATEMENT, DisclosureType.CAPITAL_INCREASE, DisclosureType.CAPITAL_DECREASE, DisclosureType.DIVIDEND]: return DisclosureSeverity.MEDIUM
        elif d_type in [DisclosureType.CONTRACT_TENDER, DisclosureType.MANAGEMENT_CHANGE]: return DisclosureSeverity.LOW
        else: return DisclosureSeverity.INFO

    def confidence_for_classification(self, record: DisclosureRecord) -> float:
        conf = 50.0
        if record.disclosure_type != DisclosureType.UNKNOWN: conf += 25.0
        if record.sentiment != DisclosureSentiment.UNKNOWN and record.sentiment != DisclosureSentiment.NEUTRAL: conf += 25.0
        return conf