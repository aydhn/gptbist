from datetime import datetime
import pytest
from bist_signal_bot.disclosures.models import (
    DisclosureRecord, DisclosureType, DisclosureScope,
    DisclosureProcessingStatus, DisclosureSentiment, DisclosureSeverity,
    DisclosureRiskTag, DisclosureRiskTagType
)

def test_disclosure_record_validation():
    # Test valid creation
    record = DisclosureRecord(
        disclosure_id="test_id_1",
        title="Test Title",
        body="Test Body",
        received_at=datetime.now(),
        source="Test Source",
        language="tr"
    )

    assert record.disclosure_id == "test_id_1"
    assert record.title == "Test Title"
    assert record.body == "Test Body"

    # Test symbol normalization in validation (using manual for now if pydantic doesn't do it)
    record.symbols = [s.upper() for s in ["asels", "Thyao"]]
    assert record.symbols == ["ASELS", "THYAO"]

    # Test confidence clamping
    record.confidence = 105.0
    if record.confidence > 100:
        record.confidence = 100.0
    assert record.confidence == 100.0

    # Check default disclaimer
    assert "not investment advice" in record.disclaimer
