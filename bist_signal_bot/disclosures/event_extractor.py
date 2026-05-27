import re
import uuid
from typing import List, Any
from datetime import datetime
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.disclosures.models import (
    DisclosureRecord, DisclosureEventExtraction, DisclosureSeverity, DisclosureProcessingStatus
)

try:
    from bist_signal_bot.events.models import MarketEvent, MarketEventType
except ImportError:
    MarketEvent = None
    MarketEventType = None

class DisclosureEventExtractor:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def extract_events(self, record: DisclosureRecord) -> List[DisclosureEventExtraction]:
        extractions = []
        dates = self.extract_dates(record.body)
        event_date = dates[0] if dates else record.published_at
        event_type = self.map_disclosure_to_event_type(record)

        extraction = DisclosureEventExtraction(
            extraction_id=str(uuid.uuid4()), disclosure_id=record.disclosure_id,
            extracted_event_type=event_type, event_date=event_date, symbols=record.symbols,
            severity=record.severity, confidence=80.0 if dates else 50.0, suggested_title=record.title[:100]
        )
        if not dates: extraction.warnings.append("No date found in text, fell back to published_at")
        extraction.should_create_market_event = self.should_create_event(extraction)
        extractions.append(extraction)
        record.status = DisclosureProcessingStatus.EVENT_EXTRACTED
        return extractions

    def extract_dates(self, text: str) -> List[datetime]:
        dates = []
        matches = re.finditer(r'(\d{1,2})[\./-](\d{1,2})[\./-](\d{4})', text)
        for m in matches:
            try:
                day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
                dates.append(datetime(year, month, day))
            except ValueError:
                pass
        return dates

    def map_disclosure_to_event_type(self, record: DisclosureRecord) -> str:
        dt = record.disclosure_type.value
        mapping = {"FINANCIAL_STATEMENT": "EARNINGS", "DIVIDEND": "DIVIDEND", "CAPITAL_INCREASE": "CORPORATE_ACTION", "CAPITAL_DECREASE": "CORPORATE_ACTION", "MACRO": "MACRO"}
        return mapping.get(dt, "OTHER")

    def should_create_event(self, extraction: DisclosureEventExtraction) -> bool:
        if extraction.extracted_event_type in ["EARNINGS", "DIVIDEND", "CORPORATE_ACTION"]:
            if extraction.event_date is not None: return True
        return False

    def to_market_event(self, extraction: DisclosureEventExtraction, record: DisclosureRecord) -> Any:
        if MarketEvent is None or MarketEventType is None: return None
        try: ev_type = MarketEventType(extraction.extracted_event_type)
        except ValueError: ev_type = MarketEventType.OTHER
        return MarketEvent(
            event_id=str(uuid.uuid4()), symbol=extraction.symbols[0] if extraction.symbols else "UNKNOWN",
            event_type=ev_type, event_date=extraction.event_date or datetime.now(), title=extraction.suggested_title,
            scope="SYMBOL" if extraction.symbols else "MARKET", description=record.title,
            source="DISCLOSURE_INTELLIGENCE", source_ref=record.disclosure_id, metadata={"disclosure_id": record.disclosure_id}
        )