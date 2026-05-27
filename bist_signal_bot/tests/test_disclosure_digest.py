import pytest
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureSeverity, DisclosureDigest
from bist_signal_bot.disclosures.digest import DisclosureDigestBuilder

def test_digest_builder():
    builder = DisclosureDigestBuilder()

    records = [
        DisclosureRecord(disclosure_id="1", title="A", body="A", symbols=["ASELS"], severity=DisclosureSeverity.HIGH),
        DisclosureRecord(disclosure_id="2", title="B", body="B", symbols=["GARAN"], severity=DisclosureSeverity.LOW)
    ]

    digest = builder.build_digest(records, title="Daily Digest")

    assert digest.title == "Daily Digest"
    assert len(digest.symbols_covered) == 2
    assert "ASELS" in digest.symbols_covered
    assert "GARAN" in digest.symbols_covered
    assert digest.high_severity_count == 1
    assert "Toplam 2 adet duyuru" in digest.summary
