from typing import Any, List
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureEntityLink

class DisclosureEntityLinker:
    def link_entities(self, record: DisclosureRecord) -> List[DisclosureEntityLink]:
        links = []
        links.extend(self.link_symbols(record))
        links.extend(self.link_company_names(record))
        return links

    def link_symbols(self, record: DisclosureRecord) -> List[DisclosureEntityLink]:
        links = []
        for symbol in record.symbols:
            links.append(DisclosureEntityLink(
                link_id=f"lnk_{symbol}",
                disclosure_id=record.disclosure_id,
                entity_type="SYMBOL",
                entity_value=symbol,
                symbol=symbol,
                relationship="PRIMARY",
                confidence=100.0
            ))
        return links

    def link_company_names(self, record: DisclosureRecord) -> List[DisclosureEntityLink]:
        links = []
        text = (record.title + " " + record.body).lower()
        if "aselsan" in text:
            links.append(DisclosureEntityLink(
                link_id="lnk_aselsan",
                disclosure_id=record.disclosure_id,
                entity_type="COMPANY_NAME",
                entity_value="ASELSAN",
                symbol="ASELS",
                relationship="INFERRED",
                confidence=90.0
            ))
        elif "bank" in text:
             links.append(DisclosureEntityLink(
                link_id="lnk_bank",
                disclosure_id=record.disclosure_id,
                entity_type="COMPANY_NAME",
                entity_value="bank",
                symbol=None,
                relationship="AMBIGUOUS",
                confidence=20.0,
                warnings=["Ambiguous company name detected: 'bank'"]
            ))
        return links

    def link_sectors(self, record: DisclosureRecord) -> List[DisclosureEntityLink]:
        return []

    def resolve_with_instrument_master(self, text: str) -> List[dict[str, Any]]:
        return []
