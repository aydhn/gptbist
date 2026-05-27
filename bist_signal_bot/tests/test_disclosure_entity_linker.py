import pytest
from bist_signal_bot.disclosures.entity_linker import DisclosureEntityLinker
from bist_signal_bot.disclosures.models import DisclosureRecord
from datetime import datetime

def test_disclosure_entity_linker_instrument_master():
    linker = DisclosureEntityLinker()
    # Mock instrument master mapping ASELSAN -> ASELS
    record = DisclosureRecord(disclosure_id="1", title="Test", body="Aselsan ihale kazandı.", received_at=datetime.now(), source="test", language="tr")
    links = linker.link_entities(record)
    symbols = [l.symbol for l in links if l.symbol]
    assert "ASELS" in symbols

def test_disclosure_entity_linker_ambiguous():
    linker = DisclosureEntityLinker()
    record = DisclosureRecord(disclosure_id="1", title="Test", body="Bank ihale kazandı.", received_at=datetime.now(), source="test", language="tr")
    links = linker.link_entities(record)
    warnings = []
    for l in links:
        warnings.extend(l.warnings)
    assert any("ambiguous" in w.lower() for w in warnings)
