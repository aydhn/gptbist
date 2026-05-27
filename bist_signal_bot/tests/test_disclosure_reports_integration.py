import pytest
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureRiskTag, DisclosureDigest, DisclosureSeverity
from bist_signal_bot.disclosures.reporting import format_disclosure_report_markdown

def test_markdown_report_generation():
    records = [
        DisclosureRecord(disclosure_id="1", title="Test 1", body="Body 1", severity=DisclosureSeverity.HIGH),
        DisclosureRecord(disclosure_id="2", title="Test 2", body="Body 2", severity=DisclosureSeverity.LOW)
    ]
    tags = []

    digest = DisclosureDigest(
        digest_id="dig_1", title="Daily Summary", summary="Overall looks stable.", high_severity_count=1
    )

    md = format_disclosure_report_markdown(records, tags, digests=[digest])

    # Needs to mention the required strings
    assert "Yatırım tavsiyesi değildir" in md
    assert "Gerçek emir gönderilmedi" in md
    assert "Toplam Duyuru: 2" in md
    assert "Daily Summary" in md
    assert "Test 1" in md
