import pytest
from datetime import datetime
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureType, DisclosureProcessingStatus

def test_disclosure_record_validation():
    # Empty title
    with pytest.raises(ValueError):
        DisclosureRecord(disclosure_id="123", title="", body="Some body")

    # Empty body
    with pytest.raises(ValueError):
        DisclosureRecord(disclosure_id="123", title="Some title", body="")

    # Symbol normalization
    rec = DisclosureRecord(
        disclosure_id="123",
        title="Title",
        body="Body",
        symbols=[" asels ", "thyao", ""]
    )
    assert rec.symbols == ["ASELS", "THYAO"]
    assert rec.status == DisclosureProcessingStatus.RAW_IMPORTED
    assert rec.disclosure_type == DisclosureType.UNKNOWN

    # Missing source warning
    assert "source_missing" in rec.warnings

def test_disclosure_record_confidence():
    rec = DisclosureRecord(
        disclosure_id="123",
        title="Title",
        body="Body",
        confidence=150.0
    )
    assert rec.confidence == 100.0

    rec = DisclosureRecord(
        disclosure_id="123",
        title="Title",
        body="Body",
        confidence=-50.0
    )
    assert rec.confidence == 0.0
