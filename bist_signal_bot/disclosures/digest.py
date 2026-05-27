import uuid
from typing import List, Dict
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.disclosures.models import (
    DisclosureRecord, DisclosureDigest, DisclosureRiskTag, DisclosureSeverity, DisclosureProcessingStatus
)

class DisclosureDigestBuilder:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def build_digest(self, records: List[DisclosureRecord], title: str | None = None) -> DisclosureDigest:
        max_records = getattr(self.settings, 'DISCLOSURE_DIGEST_MAX_RECORDS', 50)
        records = records[:max_records]

        symbols_covered = []
        for r in records: symbols_covered.extend(r.symbols)
        symbols_covered = list(set(symbols_covered))

        high_severity = self.high_severity_records(records)
        digest = DisclosureDigest(
            digest_id=str(uuid.uuid4()), title=title or f"Disclosure Digest ({len(records)} records)",
            disclosures=records, summary=self.summarize_records(records), key_points=self.key_points(records),
            symbols_covered=symbols_covered, high_severity_count=len(high_severity)
        )
        for r in records: r.status = DisclosureProcessingStatus.DIGESTED
        return digest

    def key_points(self, records: List[DisclosureRecord]) -> List[str]:
        points = []
        max_chars = getattr(self.settings, 'DISCLOSURE_DIGEST_MAX_BODY_CHARS', 1500)
        total_chars = 0
        for r in self.high_severity_records(records):
            point = f"[{r.disclosure_type.value}] {r.title}"
            if total_chars + len(point) > max_chars: break
            points.append(point)
            total_chars += len(point)
        return points

    def summarize_records(self, records: List[DisclosureRecord]) -> str:
        total = len(records)
        if total == 0: return "No disclosures provided."
        high_sev = len(self.high_severity_records(records))
        return f"Analyzed {total} disclosures. Found {high_sev} high/critical severity items."

    def group_by_symbol(self, records: List[DisclosureRecord]) -> Dict[str, List[DisclosureRecord]]:
        groups = {}
        for r in records:
            if not r.symbols: groups.setdefault("MARKET", []).append(r)
            else:
                for sym in r.symbols: groups.setdefault(sym, []).append(r)
        return groups

    def high_severity_records(self, records: List[DisclosureRecord]) -> List[DisclosureRecord]:
        return [r for r in records if r.severity in [DisclosureSeverity.HIGH, DisclosureSeverity.CRITICAL]]