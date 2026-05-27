import re
from typing import List
from datetime import datetime
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureProcessingStatus
from bist_signal_bot.security.redaction import SecretRedactor

class DisclosureNormalizer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def normalize(self, record: DisclosureRecord) -> DisclosureRecord:
        record.title = self.normalize_text(record.title)
        record.body = self.normalize_text(record.body)
        extracted_syms = self.extract_candidate_symbols(record.title + " " + record.body)
        record.symbols = self.normalize_symbols(list(set(record.symbols + extracted_syms)))
        record = self.normalize_dates(record)
        record.status = DisclosureProcessingStatus.NORMALIZED

        if len(record.body) > 50000:
            record.warnings.append("Body truncated due to excessive length")
            record.body = record.body[:50000]

        return record

    def normalize_text(self, text: str) -> str:
        if not text: return ""
        text = self.redact_sensitive_text(text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def normalize_symbols(self, symbols: List[str]) -> List[str]:
        return [s.strip().upper() for s in symbols if s and s.strip()]

    def extract_candidate_symbols(self, text: str) -> List[str]:
        candidates = re.findall(r'[A-Z]{4,5}', text)
        return candidates

    def normalize_dates(self, record: DisclosureRecord) -> DisclosureRecord:
        if not record.published_at:
            record.published_at = record.received_at
        return record

    def redact_sensitive_text(self, text: str) -> str:
        return text