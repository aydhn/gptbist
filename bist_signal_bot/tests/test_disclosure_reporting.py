from bist_signal_bot.disclosures.reporting import format_disclosure_report_markdown, risk_tag_to_dict
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureRiskTag, DisclosureRiskTagType, DisclosureSeverity, DisclosureSentiment
def test_markdown_report():
    r = DisclosureRecord(disclosure_id="1", title="Title", body="Body", source="c")
    t = DisclosureRiskTag(tag_id="2", disclosure_id="1", tag_type=DisclosureRiskTagType.LIQUIDITY_PRESSURE, severity=DisclosureSeverity.HIGH, sentiment="NEGATIVE", message="msg")
    md = format_disclosure_report_markdown([r], [t])
    assert "Title" in md

def test_risk_tag_to_dict():
    t = DisclosureRiskTag(
        tag_id="2",
        disclosure_id="1",
        tag_type=DisclosureRiskTagType.LIQUIDITY_PRESSURE,
        severity=DisclosureSeverity.HIGH,
        sentiment=DisclosureSentiment.NEGATIVE,
        message="msg"
    )
    d = risk_tag_to_dict(t)
    assert d["tag_id"] == "2"
    assert d["disclosure_id"] == "1"
    assert d["tag_type"] == DisclosureRiskTagType.LIQUIDITY_PRESSURE.value
    assert d["severity"] == DisclosureSeverity.HIGH.value
    assert d["sentiment"] == DisclosureSentiment.NEGATIVE.value
    assert d["message"] == "msg"
    assert "warnings" in d
    assert "metadata" in d
