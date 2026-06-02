import uuid
from typing import List, Optional
from bist_signal_bot.report_templates.models import ReportNarrativeBlock, ReportValidationStatus

class ReportNarrativeGuard:
    def __init__(self, settings=None):
        self.settings = settings
        self.unsafe_keywords = [
            "al", "sat", "kesin al", "kesin sat", "hedef fiyat", "trade ready",
            "işlem yapılabilir", "yatırım tavsiyesidir", "canlı işlem için hazır",
            "guaranteed return", "live deployment approved"
        ]

    def build_narrative_block(self, title: str, text: str, source_refs: Optional[List[str]] = None) -> ReportNarrativeBlock:
        safe_status = ReportValidationStatus.PASS
        warnings = []
        unsafe = self.detect_unsafe_language(text)

        if unsafe:
            safe_status = ReportValidationStatus.BLOCKED
            warnings.append(f"Unsafe language detected: {', '.join(unsafe)}")
            if getattr(self.settings, 'REPORT_NARRATIVE_REWRITE_UNSAFE_SUMMARY', True):
                text = self.rewrite_to_safe_summary(text)
                warnings.append("Text was automatically rewritten to safe summary.")

        return ReportNarrativeBlock(
            block_id=f"nar_{uuid.uuid4().hex[:8]}",
            title=title,
            text=text,
            source_refs=source_refs or [],
            safe_language_status=safe_status,
            warnings=warnings
        )

    def safe_text(self, text: str) -> str:
        unsafe = self.detect_unsafe_language(text)
        if unsafe:
            return self.rewrite_to_safe_summary(text)
        return text

    def detect_unsafe_language(self, text: str) -> List[str]:
        text_lower = text.lower()
        findings = []
        for kw in self.unsafe_keywords:
            if kw in text_lower:
                findings.append(kw)
        return findings

    def validate_narrative(self, block: ReportNarrativeBlock) -> List[str]:
        return block.warnings

    def rewrite_to_safe_summary(self, text: str) -> str:
        # Simple deterministic rewrite rule
        return "[REDACTED] This text contained unsafe language and was rewritten. This is local research metadata only."
