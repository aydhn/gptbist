from bist_signal_bot.disclosures.risk_tags import DisclosureRiskTagger
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureRiskTagType
def test_risk_tags():
    tagger = DisclosureRiskTagger()
    rec = DisclosureRecord(disclosure_id="1", title="Dava", body="Büyük zarar, ayrıca bedelli yapılacak. Kredi notumuz düştü, borç çok.", source="c")
    tags = tagger.tag(rec)
    types = [t.tag_type for t in tags]
    assert DisclosureRiskTagType.EARNINGS_VOLATILITY in types
    assert DisclosureRiskTagType.LEGAL_REGULATORY in types
