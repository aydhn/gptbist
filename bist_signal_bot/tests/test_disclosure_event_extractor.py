import pytest
from bist_signal_bot.disclosures.event_extractor import DisclosureEventExtractor
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureType
from datetime import datetime

def test_disclosure_event_extractor_date():
    extractor = DisclosureEventExtractor()
    record = DisclosureRecord(disclosure_id="1", title="Genel Kurul", body="Toplantı 25.12.2023 tarihinde yapılacaktır.", disclosure_type=DisclosureType.GENERAL_ASSEMBLY, received_at=datetime.now(), source="test", language="tr")
    events = extractor.extract_events(record)
    assert len(events) > 0
    assert events[0].event_date.year == 2023

def test_disclosure_event_extractor_fallback_date():
    extractor = DisclosureEventExtractor()
    pub_date = datetime(2023, 1, 1)
    record = DisclosureRecord(disclosure_id="1", title="Duyuru", body="Yakında açıklanacak.", published_at=pub_date, received_at=datetime.now(), source="test", language="tr")
    events = extractor.extract_events(record)
    if events:
        assert events[0].event_date == pub_date
        assert any("fallback" in w.lower() for w in events[0].warnings)
