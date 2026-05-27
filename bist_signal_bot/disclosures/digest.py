from typing import List, Dict, Optional
from datetime import datetime
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureDigest, DisclosureSeverity

class DisclosureDigestBuilder:
    def build_digest(self, records: List[DisclosureRecord], title: Optional[str] = None) -> DisclosureDigest:
        high_severity_count = len(self.high_severity_records(records))
        symbols_covered = list(set([s for r in records for s in r.symbols]))

        return DisclosureDigest(
            digest_id=f"dig_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            created_at=datetime.now(),
            title=title or "Disclosure Digest",
            disclosures=records,
            summary=self.summarize_records(records),
            key_points=self.key_points(records),
            risk_tags=[],
            symbols_covered=symbols_covered,
            high_severity_count=high_severity_count
        )

    def key_points(self, records: List[DisclosureRecord]) -> List[str]:
        return [r.title for r in records[:5]]

    def summarize_records(self, records: List[DisclosureRecord]) -> str:
        if not records:
            return "No records to summarize."
        return f"Summarized {len(records)} records. Top record: {records[0].title}"

    def group_by_symbol(self, records: List[DisclosureRecord]) -> Dict[str, List[DisclosureRecord]]:
        grouped = {}
        for r in records:
            for s in r.symbols:
                grouped.setdefault(s, []).append(r)
        return grouped

    def high_severity_records(self, records: List[DisclosureRecord]) -> List[DisclosureRecord]:
        return [r for r in records if r.severity in [DisclosureSeverity.HIGH, DisclosureSeverity.CRITICAL]]
