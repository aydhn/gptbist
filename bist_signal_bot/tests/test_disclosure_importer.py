import pytest
import json
from pathlib import Path
from bist_signal_bot.disclosures.importer import DisclosureImporter

@pytest.fixture
def test_csv(tmp_path):
    f = tmp_path / "test.csv"
    f.write_text("title,body,symbols,disclosure_type\nTitle 1,Body 1,ASELS,FINANCIAL_STATEMENT\n")
    return f

def test_importer_parse_csv(test_csv):
    importer = DisclosureImporter()
    records = importer.parse_csv(test_csv)
    assert len(records) == 1
    assert records[0].title == "Title 1"
    assert records[0].symbols == ["ASELS"]

def test_importer_requires_confirm(test_csv):
    importer = DisclosureImporter()
    res = importer.import_file(test_csv, confirm=False)
    assert res.disclosures_imported == 0
    assert any("Confirm flag not set" in w for w in res.warnings)
