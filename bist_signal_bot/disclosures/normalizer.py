import re
from bist_signal_bot.disclosures.models import DisclosureRecord

class DisclosureNormalizer:
    def normalize(self, record: DisclosureRecord) -> DisclosureRecord:
        record.title = self.normalize_text(record.title)
        record.body = self.normalize_text(record.body)

        record.title = self.redact_sensitive_text(record.title)
        record.body = self.redact_sensitive_text(record.body)

        record.symbols = self.normalize_symbols(record.symbols)
        return self.normalize_dates(record)

    def normalize_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def normalize_symbols(self, symbols: list[str]) -> list[str]:
        return [s.strip().upper() for s in symbols if s.strip()]

    def extract_candidate_symbols(self, text: str) -> list[str]:
        return []

    def normalize_dates(self, record: DisclosureRecord) -> DisclosureRecord:
        return record

    def redact_sensitive_text(self, text: str) -> str:
        # Example pattern for redaction
        text = re.sub(r'\b[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}\b', '[REDACTED]', text)
        text = re.sub(r'\b(api|token|secret|password|key)\s*[:=]\s*\S+', r'\1: [REDACTED]', text, flags=re.IGNORECASE)
        return text
