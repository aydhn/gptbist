import uuid
from datetime import datetime
from typing import List, Optional, Dict
from bist_signal_bot.disclosures.models import (
    DisclosureRecord,
    DisclosureDigest,
    DisclosureSeverity,
    DisclosureRiskTag
)

class DisclosureDigestBuilder:
    def __init__(self, settings=None):
        self.settings = settings

    def build_digest(self, records: List[DisclosureRecord], title: Optional[str] = None) -> DisclosureDigest:
        digest = DisclosureDigest(
            digest_id=f"dig_{uuid.uuid4().hex[:8]}",
            title=title or f"Disclosure Digest {datetime.now().strftime('%Y-%m-%d')}",
            disclosures=records
        )

        digest.summary = self.summarize_records(records)
        digest.key_points = self.key_points(records)

        symbols = set()
        for r in records:
            symbols.update(r.symbols)
        digest.symbols_covered = sorted(list(symbols))

        digest.high_severity_count = len(self.high_severity_records(records))

        # Risk tags would normally be passed in or collected from store, simplifying here
        return digest

    def key_points(self, records: List[DisclosureRecord]) -> List[str]:
        points = []
        high_sev = self.high_severity_records(records)
        for r in high_sev[:5]: # Limit to top 5
            points.append(f"[{','.join(r.symbols)}] {r.title}")

        if not points and records:
            points.append(f"{len(records)} adet genel duyuru işlendi.")

        return points

    def summarize_records(self, records: List[DisclosureRecord]) -> str:
        if not records:
            return "Duyuru bulunamadı."
        return f"Toplam {len(records)} adet duyuru işlenmiştir. Bu metin otomatik özetlemedir, yatırım tavsiyesi içermez."

    def group_by_symbol(self, records: List[DisclosureRecord]) -> Dict[str, List[DisclosureRecord]]:
        groups = {}
        for r in records:
            for sym in r.symbols:
                if sym not in groups:
                    groups[sym] = []
                groups[sym].append(r)
        return groups

    def high_severity_records(self, records: List[DisclosureRecord]) -> List[DisclosureRecord]:
        return [r for r in records if r.severity in [DisclosureSeverity.HIGH, DisclosureSeverity.CRITICAL]]
