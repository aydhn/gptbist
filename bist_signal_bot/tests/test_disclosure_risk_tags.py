import pytest
from bist_signal_bot.disclosures.models import DisclosureRecord
from bist_signal_bot.disclosures.risk_tags import DisclosureRiskTagger

def test_risk_tagger():
    tagger = DisclosureRiskTagger()

    record = DisclosureRecord(
        disclosure_id="123",
        title="Dava süreci",
        body="Şirket aleyhine dava açıldı. Nakit sıkıntısı var."
    )

    tags = tagger.tag(record)
    tag_types = [t.tag_type.value for t in tags]

    assert "LEGAL_REGULATORY" in tag_types
    assert "LIQUIDITY_PRESSURE" in tag_types
