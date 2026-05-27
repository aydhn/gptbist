import pytest
from bist_signal_bot.disclosures.models import DisclosureRecord
from bist_signal_bot.disclosures.normalizer import DisclosureNormalizer

def test_normalizer():
    normalizer = DisclosureNormalizer()

    record = DisclosureRecord(
        disclosure_id="123",
        title="  A  title \n with space  ",
        body="Some token = 'secret1234567890abcdef'",
        symbols=[" asels ", "thyao"]
    )

    record = normalizer.normalize(record)

    assert record.title == "A title with space"
    assert "[REDACTED]" in record.body
    assert record.symbols == ["ASELS", "THYAO"]

    # Check candidate symbols
    record2 = DisclosureRecord(
        disclosure_id="124", title="T", body="GARAN and KCHOL are mentioned."
    )
    record2 = normalizer.normalize(record2)
    assert "GARAN" in record2.symbols
    assert "KCHOL" in record2.symbols
