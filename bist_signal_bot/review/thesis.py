import uuid
import re
from datetime import datetime, timezone
from typing import List, Optional

from .models import ReviewThesis, ThesisStrength, ReviewEvidence

class ReviewThesisBuilder:
    def __init__(self, settings=None):
        self.settings = settings

    def create_thesis(self, item_id: str, symbol: str, main_thesis: str,
                      counter_thesis: str = "", key_risks: Optional[List[str]] = None,
                      invalidation_points: Optional[List[str]] = None) -> ReviewThesis:

        sanitized_main = self.sanitize_thesis_text(main_thesis)
        sanitized_counter = self.sanitize_thesis_text(counter_thesis)

        now = datetime.now(timezone.utc)
        return ReviewThesis(
            thesis_id=str(uuid.uuid4()),
            item_id=item_id,
            symbol=symbol.upper(),
            created_at=now,
            updated_at=now,
            main_thesis=sanitized_main,
            counter_thesis=sanitized_counter,
            key_risks=key_risks or [],
            invalidation_points=invalidation_points or []
        )

    def update_thesis(self, thesis_id: str, main_thesis: Optional[str] = None,
                      counter_thesis: Optional[str] = None, key_risks: Optional[List[str]] = None,
                      invalidation_points: Optional[List[str]] = None) -> ReviewThesis:
        # In a real app, this would fetch from store. Here we mock it.
        # It's better to pass the thesis object.
        pass

    def score_thesis_strength(self, thesis: ReviewThesis, evidence: List[ReviewEvidence]) -> ThesisStrength:

        if not thesis.main_thesis:
            return ThesisStrength.WEAK
        if thesis.counter_thesis and len(thesis.counter_thesis) > len(thesis.main_thesis):
            return ThesisStrength.CONFLICTED
        if thesis.key_risks and len(thesis.key_risks) >= 3:
            return ThesisStrength.MODERATE
        return ThesisStrength.STRONG

    def sanitize_thesis_text(self, text: str) -> str:
        if not text:
            return ""
        # Remove unsafe claims
        unsafe_patterns = [
            r"kesin(lik)?\s?(al|sat)",
            r"garanti(li)?\s?(kazanç|getiri)",
            r"fırsat",
            r"kaçmaz",
            r"100%"
        ]
        sanitized = text
        for pattern in unsafe_patterns:
            sanitized = re.sub(pattern, "[REDACTED_CLAIM]", sanitized, flags=re.IGNORECASE)

        return sanitized
