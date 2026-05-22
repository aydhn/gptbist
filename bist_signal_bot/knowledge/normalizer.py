import re
from collections import Counter

class KnowledgeTextNormalizer:

    def __init__(self):
        # Basic Turkish char mapping for normalization
        self.tr_map = {
            'ç': 'c', 'Ç': 'C',
            'ğ': 'g', 'Ğ': 'G',
            'ı': 'i', 'İ': 'I',
            'ö': 'o', 'Ö': 'O',
            'ş': 's', 'Ş': 'S',
            'ü': 'u', 'Ü': 'U'
        }

        # Stopwords (lightweight list to avoid external dependencies like NLTK)
        self.stopwords = {
            've', 'ile', 'veya', 'ama', 'fakat', 'lakin', 'ancak', 'bu', 'su', 'o',
            'icin', 'gibi', 'kadar', 'gore', 'ise', 'da', 'de', 'ki', 'mi', 'mu',
            'bir', 'iki', 'uc', 'dort', 'bes', 'olan', 'olarak', 'oldu', 'olacak'
        }

    def normalize_turkish_chars(self, text: str) -> str:
        res = text
        for k, v in self.tr_map.items():
            res = res.replace(k, v)
        return res

    def sanitize_text(self, text: str) -> str:
        """Removes potential secrets/credentials (very basic pass, relies on core for deep redaction)."""
        # Strip simple identifiable patterns
        text = re.sub(r'([a-zA-Z0-9_-]{20,})', '[REDACTED]', text)
        return text

    def normalize_text(self, text: str) -> str:
        text = self.sanitize_text(text)
        text = self.normalize_turkish_chars(text.lower())
        # Keep alphanumeric, remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def extract_terms(self, text: str) -> dict[str, int]:
        norm = self.normalize_text(text)
        tokens = norm.split()
        filtered = self.remove_stopwords(tokens)
        return dict(Counter(filtered))

    def remove_stopwords(self, tokens: list[str]) -> list[str]:
        return [t for t in tokens if t not in self.stopwords and len(t) > 1]

    def safe_snippet(self, text: str, query: str | None = None, max_chars: int = 300) -> str:
        text = self.sanitize_text(text)
        if len(text) <= max_chars:
            return text

        if query:
            query_terms = list(self.extract_terms(query).keys())
            # Find first match
            first_match = -1
            lower_text = self.normalize_turkish_chars(text.lower())
            for q in query_terms:
                idx = lower_text.find(q)
                if idx != -1 and (first_match == -1 or idx < first_match):
                    first_match = idx

            if first_match != -1:
                start = max(0, first_match - 50)
                end = min(len(text), start + max_chars)
                snippet = text[start:end]
                if start > 0: snippet = "..." + snippet
                if end < len(text): snippet = snippet + "..."
                return snippet

        # Fallback to prefix
        return text[:max_chars] + "..."
