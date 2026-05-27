import uuid
from typing import List, Any, Dict
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureEntityLink

class DisclosureEntityLinker:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir
        # Ideally, we would inject InstrumentMaster here, but we will mock its behavior for the module

    def link_entities(self, record: DisclosureRecord) -> List[DisclosureEntityLink]:
        links = []
        links.extend(self.link_symbols(record))
        links.extend(self.link_company_names(record))
        links.extend(self.link_sectors(record))
        return links

    def link_symbols(self, record: DisclosureRecord) -> List[DisclosureEntityLink]:
        links = []
        for sym in record.symbols:
            links.append(DisclosureEntityLink(
                link_id=f"lnk_{uuid.uuid4().hex[:8]}",
                disclosure_id=record.disclosure_id,
                entity_type="SYMBOL",
                entity_value=sym,
                symbol=sym,
                confidence=100.0,
                relationship="EXPLICIT_MENTION"
            ))
        return links

    def link_company_names(self, record: DisclosureRecord) -> List[DisclosureEntityLink]:
        links = []
        for name in record.company_names:
            # Fallback mapping or mocked instrument master resolution
            resolved = self.resolve_with_instrument_master(name)
            sym = resolved[0]['symbol'] if resolved else None

            link = DisclosureEntityLink(
                link_id=f"lnk_{uuid.uuid4().hex[:8]}",
                disclosure_id=record.disclosure_id,
                entity_type="COMPANY",
                entity_value=name,
                symbol=sym,
                confidence=80.0 if sym else 40.0,
                relationship="COMPANY_MENTION"
            )
            if len(resolved) > 1:
                link.warnings.append("ambiguous_company_name")

            links.append(link)
        return links

    def link_sectors(self, record: DisclosureRecord) -> List[DisclosureEntityLink]:
        links = []
        for sector in record.sectors:
            links.append(DisclosureEntityLink(
                link_id=f"lnk_{uuid.uuid4().hex[:8]}",
                disclosure_id=record.disclosure_id,
                entity_type="SECTOR",
                entity_value=sector,
                relationship="SECTOR_MENTION",
                confidence=90.0
            ))
        return links

    def resolve_with_instrument_master(self, text: str) -> List[Dict[str, Any]]:
        # Mocking instrument master resolution. In real code, it queries the master.
        # This deterministic mock just maps a few common strings to symbols.
        text_lower = text.lower()
        if "aselsan" in text_lower:
            return [{"symbol": "ASELS", "name": "Aselsan"}]
        if "garanti" in text_lower:
            return [{"symbol": "GARAN", "name": "Garanti Bankası"}]
        return []
