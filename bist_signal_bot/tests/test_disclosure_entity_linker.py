import pytest
from bist_signal_bot.disclosures.models import DisclosureRecord
from bist_signal_bot.disclosures.entity_linker import DisclosureEntityLinker

def test_entity_linker_symbols():
    linker = DisclosureEntityLinker()

    record = DisclosureRecord(
        disclosure_id="123", title="A", body="A", symbols=["ASELS", "THYAO"], company_names=["Garanti Bankası"]
    )

    links = linker.link_entities(record)

    # 2 symbols + 1 company = 3 links
    assert len(links) == 3

    symbol_links = [l for l in links if l.entity_type == "SYMBOL"]
    assert len(symbol_links) == 2

    company_links = [l for l in links if l.entity_type == "COMPANY"]
    assert len(company_links) == 1

    assert company_links[0].symbol == "GARAN"  # Due to mock resolution
