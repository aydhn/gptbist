import pytest
from datetime import datetime
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureType, DisclosureSeverity
from bist_signal_bot.disclosures.event_extractor import DisclosureEventExtractor

def test_extract_events():
    extractor = DisclosureEventExtractor()
    record = DisclosureRecord(
        disclosure_id="123",
        title="Genel Kurul Toplantısı 15.05.2024 tarihinde",
        body="Şirketimizin olağan genel kurulu 15.05.2024'te yapılacaktır.",
        disclosure_type=DisclosureType.GENERAL_ASSEMBLY,
        severity=DisclosureSeverity.HIGH
    )

    extractions = extractor.extract_events(record)
    assert len(extractions) == 1
    ext = extractions[0]

    assert ext.extracted_event_type == "GENERAL_ASSEMBLY"
    assert ext.event_date == datetime(2024, 5, 15)
    assert ext.should_create_market_event is True

def test_extract_events_fallback_date():
    extractor = DisclosureEventExtractor()
    record = DisclosureRecord(
        disclosure_id="123",
        title="Bilanço açıklandı",
        body="Bilanço detayları.",
        published_at=datetime(2024, 4, 1),
        disclosure_type=DisclosureType.FINANCIAL_STATEMENT
    )

    extractions = extractor.extract_events(record)
    assert len(extractions) == 1
    ext = extractions[0]

    assert ext.event_date == datetime(2024, 4, 1)
    assert "no_event_date_found" in ext.warnings
