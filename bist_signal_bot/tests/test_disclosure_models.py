import pytest
from pydantic import ValidationError
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureType

def test_disclosure_record_validation():
    rec = DisclosureRecord(
        disclosure_id="123",
        title="Test Title",
        body="Test Body",
        symbols=["asels ", " thyao"],
        source="TEST"
    )
    assert rec.symbols == ["ASELS", "THYAO"]
    assert rec.disclosure_type == DisclosureType.UNKNOWN

    with pytest.raises(ValidationError):
        DisclosureRecord(
            disclosure_id="124",
            title="   ",
            body="Test Body",
            source="TEST"
        )
