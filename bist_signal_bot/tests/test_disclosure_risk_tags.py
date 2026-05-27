import pytest
from bist_signal_bot.disclosures.risk_tags import DisclosureRiskTagger
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureRiskTagType
from datetime import datetime

def test_disclosure_risk_tagger_debt():
    tagger = DisclosureRiskTagger()
    record = DisclosureRecord(disclosure_id="1", title="Borç", body="Borç yapılandırması yapıldı, temerrüt riski.", received_at=datetime.now(), source="test", language="tr")
    tags = tagger.tag(record)
    types = [t.tag_type for t in tags]
    assert DisclosureRiskTagType.LIQUIDITY_PRESSURE in types

def test_disclosure_risk_tagger_legal():
    tagger = DisclosureRiskTagger()
    record = DisclosureRecord(disclosure_id="1", title="Dava", body="Şirketimize ceza kesildi.", received_at=datetime.now(), source="test", language="tr")
    tags = tagger.tag(record)
    types = [t.tag_type for t in tags]
    assert DisclosureRiskTagType.LEGAL_REGULATORY in types

def test_disclosure_risk_tagger_dilution():
    tagger = DisclosureRiskTagger()
    record = DisclosureRecord(disclosure_id="1", title="Bedelli", body="Sermaye artırımı ve pay ihracı.", received_at=datetime.now(), source="test", language="tr")
    tags = tagger.tag(record)
    types = [t.tag_type for t in tags]
    assert DisclosureRiskTagType.DILUTION_RISK in types
