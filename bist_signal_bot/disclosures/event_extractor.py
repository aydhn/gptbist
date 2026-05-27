import re
import uuid
from datetime import datetime
from typing import List, Any
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureEventExtraction, DisclosureSeverity

class DisclosureEventExtractor:
    def __init__(self, settings=None):
        self.settings = settings

    def extract_events(self, record: DisclosureRecord) -> List[DisclosureEventExtraction]:
        extractions = []

        event_type = self.map_disclosure_to_event_type(record)
        dates = self.extract_dates(f"{record.title} {record.body}")

        event_date = dates[0] if dates else record.published_at

        extraction = DisclosureEventExtraction(
            extraction_id=f"ext_{uuid.uuid4().hex[:8]}",
            disclosure_id=record.disclosure_id,
            extracted_event_type=event_type,
            event_date=event_date,
            symbols=record.symbols.copy(),
            severity=record.severity,
            confidence=80.0 if dates else 40.0,
            suggested_title=record.title[:100]
        )

        if not dates and record.published_at:
            extraction.warnings.append("no_event_date_found")

        extraction.should_create_market_event = self.should_create_event(extraction)
        extractions.append(extraction)
        return extractions

    def extract_dates(self, text: str) -> List[datetime]:
        # Very simple regex for DD.MM.YYYY
        matches = re.findall(r'(\d{2})[./-](\d{2})[./-](\d{4})', text)
        dates = []
        for d, m, y in matches:
            try:
                dates.append(datetime(int(y), int(m), int(d)))
            except ValueError:
                pass
        return dates

    def map_disclosure_to_event_type(self, record: DisclosureRecord) -> str:
        # Maps DisclosureType to Event Calendar EventType string representations
        mapping = {
            "FINANCIAL_STATEMENT": "EARNINGS",
            "DIVIDEND": "DIVIDEND",
            "CAPITAL_INCREASE": "CORPORATE_ACTION",
            "GENERAL_ASSEMBLY": "GENERAL_ASSEMBLY"
        }
        return mapping.get(record.disclosure_type.value, "MATERIAL_EVENT")

    def should_create_event(self, extraction: DisclosureEventExtraction) -> bool:
        if not extraction.event_date:
            return False
        if extraction.severity in [DisclosureSeverity.CRITICAL, DisclosureSeverity.HIGH]:
            return True
        return False

    def to_market_event(self, extraction: DisclosureEventExtraction, record: DisclosureRecord) -> Any:
        # Normally this would return a MarketEvent model from bist_signal_bot.events.models
        # Creating a dummy dict for now to satisfy structural requirements without full import deps
        return {
            "event_type": extraction.extracted_event_type,
            "title": extraction.suggested_title,
            "date": extraction.event_date,
            "symbols": extraction.symbols,
            "source": record.source,
            "source_ref": record.disclosure_id
        }
