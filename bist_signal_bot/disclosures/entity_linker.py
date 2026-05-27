import logging
import uuid
from typing import List, Any
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureEntityLink, DisclosureProcessingStatus
try:
    from bist_signal_bot.instruments.master import InstrumentMaster
except ImportError:
    InstrumentMaster = None

logger = logging.getLogger(__name__)

class DisclosureEntityLinker:
    def __init__(self, settings: Settings | None = None, instrument_master=None):
        self.settings = settings or get_settings()
        self.instrument_master = instrument_master
        if self.instrument_master is None and InstrumentMaster is not None:
            self.instrument_master = InstrumentMaster()

    def link_entities(self, record: DisclosureRecord) -> List[DisclosureEntityLink]:
        links = []
        links.extend(self.link_symbols(record))
        links.extend(self.link_company_names(record))
        links.extend(self.link_sectors(record))
        record.status = DisclosureProcessingStatus.LINKED
        return links

    def link_symbols(self, record: DisclosureRecord) -> List[DisclosureEntityLink]:
        links = []
        for sym in record.symbols:
            resolved_sym = None
            if self.instrument_master:
                resolved_sym = self.instrument_master.resolve_symbol(sym)
                if resolved_sym: sym = resolved_sym

            links.append(DisclosureEntityLink(
                link_id=str(uuid.uuid4()), disclosure_id=record.disclosure_id, entity_type="SYMBOL",
                entity_value=sym, symbol=sym, confidence=100.0 if resolved_sym else 50.0, relationship="MENTIONED"
            ))
        return links

    def link_company_names(self, record: DisclosureRecord) -> List[DisclosureEntityLink]:
        links = []
        for name in record.company_names:
            link = DisclosureEntityLink(
                link_id=str(uuid.uuid4()), disclosure_id=record.disclosure_id, entity_type="COMPANY_NAME",
                entity_value=name, symbol=None, confidence=80.0, relationship="MENTIONED"
            )
            if self.instrument_master:
                results = self.resolve_with_instrument_master(name)
                if len(results) == 1:
                    link.symbol = results[0]["symbol"]
                    link.confidence = 90.0
                elif len(results) > 1:
                    link.warnings.append("Ambiguous company name resolution.")
            links.append(link)
        return links

    def link_sectors(self, record: DisclosureRecord) -> List[DisclosureEntityLink]:
        links = []
        for sector in record.sectors:
            links.append(DisclosureEntityLink(
                link_id=str(uuid.uuid4()), disclosure_id=record.disclosure_id, entity_type="SECTOR",
                entity_value=sector, symbol=None, confidence=90.0, relationship="AFFECTS"
            ))
        return links

    def resolve_with_instrument_master(self, text: str) -> List[dict]:
        if not self.instrument_master: return []
        results = []
        text_lower = text.lower()
        if hasattr(self.instrument_master, "_records"):
            for sym, rec in self.instrument_master._records.items():
                name_lower = getattr(rec, 'name', '').lower()
                if name_lower and name_lower in text_lower:
                    results.append({"symbol": sym})
        return results