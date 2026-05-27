import pytest
from bist_signal_bot.disclosures.digest import DisclosureDigestBuilder
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureType
from datetime import datetime

def test_disclosure_digest_builder():
    builder = DisclosureDigestBuilder()
    record = DisclosureRecord(disclosure_id="1", title="Test Title", body="Test Body", disclosure_type=DisclosureType.MATERIAL_EVENT, received_at=datetime.now(), source="test", language="tr")
    digest = builder.build_digest([record], title="Daily Digest")
    assert digest.title == "Daily Digest"
    assert "Test Title" in digest.summary
