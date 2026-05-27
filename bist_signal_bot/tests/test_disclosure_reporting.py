from bist_signal_bot.disclosures.reporting import format_disclosure_report_markdown
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureRiskTag, DisclosureRiskTagType, DisclosureSeverity
def test_markdown_report():
    r = DisclosureRecord(disclosure_id="1", title="Title", body="Body", source="c")
    t = DisclosureRiskTag(tag_id="2", disclosure_id="1", tag_type=DisclosureRiskTagType.LIQUIDITY_PRESSURE, severity=DisclosureSeverity.HIGH, sentiment="NEGATIVE", message="msg")
    md = format_disclosure_report_markdown([r], [t])
    assert "Title" in md
