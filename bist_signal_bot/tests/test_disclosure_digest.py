from bist_signal_bot.disclosures.digest import DisclosureDigestBuilder
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureSeverity
def test_digest_builder():
    builder = DisclosureDigestBuilder()
    r1 = DisclosureRecord(disclosure_id="1", title="High Risk", body="b", severity=DisclosureSeverity.HIGH, source="c")
    digest = builder.build_digest([r1])
    assert digest.high_severity_count == 1
