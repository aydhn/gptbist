from bist_signal_bot.disclosures.entity_linker import DisclosureEntityLinker
from bist_signal_bot.disclosures.models import DisclosureRecord
def test_entity_linker_ambiguous():
    linker = DisclosureEntityLinker()
    class MockMaster:
        def resolve_symbol(self, sym): return sym
        _records = {"A": type('obj', (object,), {'name': 'test'})(), "B": type('obj', (object,), {'name': 'test'})()}
    linker.instrument_master = MockMaster()
    rec = DisclosureRecord(disclosure_id="1", title="a", body="b", source="c", company_names=["test"])
    links = linker.link_company_names(rec)
    assert len(links) == 1
    assert "Ambiguous" in links[0].warnings[0]
