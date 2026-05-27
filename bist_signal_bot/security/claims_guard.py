import re
from typing import Any

from bist_signal_bot.core.exceptions import UnsafeClaimError

class UnsafeClaimGuard:
    """Ensures output messages do not contain unsafe financial claims or pretend to execute real orders."""

    # Tuples of (regex_pattern, safe_replacement)
    UNSAFE_REPLACEMENTS = [
        (r'\bkesin\s+al\b', "araştırma amaçlı alım adayı"),
        (r'\bkesin\s+sat\b', "araştırma amaçlı satım adayı"),
        (r'\bgaranti\b', "garanti içermez"),
        (r'\brisksiz\s+kazan[cç]\b', "araştırma amaçlı potansiyel (risk içerir)"),
        (r'\bzararsız\b', "potansiyel zararı sınırlandırma"),
        (r'\bmutlaka\s+yükselecek\b', "yükseliş potansiyeli (araştırma adayı)"),
        (r'\bşu\s+fiyattan\s+al\b', "potansiyel alım bölgesi (araştırma)"),
        (r'\bşu\s+fiyattan\s+sat\b', "potansiyel satım bölgesi (araştırma)"),
        (r'\bemir\s+gönderildi\b', "gerçek emir gönderilmedi (simülasyon)"),
        (r'\bgerçek\s+işlem\s+açıldı\b', "sanal işlem kaydedildi (paper trade)"),
        (r'\bk[aâ]r\s+garantili\b', "garanti içermez"),
        (r'\byatırım\s+tavsiyesidir\b', "yatırım tavsiyesi değildir")
    ]

    @classmethod
    def validate_text(cls, text: str) -> None:
        """Throws an exception if unsafe claims are found."""
        if not text:
            return

        text_lower = text.lower()
        for pattern, _ in cls.UNSAFE_REPLACEMENTS:
            if re.search(pattern, text_lower):
                raise UnsafeClaimError(f"Unsafe claim detected matching pattern: {pattern}")

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """Replaces unsafe claims with safe alternatives."""
        if not text:
            return text

        sanitized = text
        for pattern, replacement in cls.UNSAFE_REPLACEMENTS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized

    @classmethod
    def validate_payload(cls, payload: Any) -> None:
        """Deeply validates a dict/list structure."""
        if isinstance(payload, dict):
            for v in payload.values():
                cls.validate_payload(v)
        elif isinstance(payload, list):
            for item in payload:
                cls.validate_payload(item)
        elif isinstance(payload, str):
            cls.validate_text(payload)

    @classmethod
    def sanitize_payload(cls, payload: Any) -> Any:
        """Deeply sanitizes a dict/list structure."""
        if isinstance(payload, dict):
            return {k: cls.sanitize_payload(v) for k, v in payload.items()}
        elif isinstance(payload, list):
            return [cls.sanitize_payload(item) for item in payload]
        elif isinstance(payload, str):
            return cls.sanitize_text(payload)
        return payload

# Added for Disclosure Integration
# Claims guard blocks phrases like 'haber sonrasi kesin fiyat hareketi'
