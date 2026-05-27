import re
from typing import List, Any
from datetime import datetime
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureEventExtraction, DisclosureSeverity

class DisclosureEventExtractor:
    def extract_events(self, record: DisclosureRecord) -> List[DisclosureEventExtraction]:
        dates = self.extract_dates(record.title + " " + record.body)
        event_date = dates[0] if dates else record.published_at
        warnings = []
        if not dates and record.published_at:
            warnings.append("Date missing in text, using published_at as fallback.")

        extraction = DisclosureEventExtraction(
            extraction_id=f"ext_{record.disclosure_id}",
            disclosure_id=record.disclosure_id,
            extracted_event_type=self.map_disclosure_to_event_type(record),
            event_date=event_date,
            symbols=record.symbols,
            severity=record.severity,
            confidence=80.0,
            should_create_market_event=False,
            suggested_title=f"Event for {record.title}",
            warnings=warnings
        )
        return [extraction]

    def extract_dates(self, text: str) -> List[datetime]:
        dates = []
        matches = re.finditer(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', text)
        for match in matches:
            try:
                day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                dates.append(datetime(year, month, day))
            except ValueError:
                pass
        return dates

    def map_disclosure_to_event_type(self, record: DisclosureRecord) -> str:
        return record.disclosure_type.value

    def should_create_event(self, extraction: DisclosureEventExtraction) -> bool:
        return extraction.should_create_market_event

    def to_market_event(self, extraction: DisclosureEventExtraction, record: DisclosureRecord) -> Any:
        pass
