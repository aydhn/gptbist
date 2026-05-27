import pytest
from pathlib import Path
from bist_signal_bot.disclosures.models import DisclosureType, DisclosureRecord
from bist_signal_bot.disclosures.importer import DisclosureImporter
from bist_signal_bot.core.exceptions import DisclosureImportError

def test_disclosure_importer_csv(tmp_path):
    importer = DisclosureImporter()
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("external_id,title,body,disclosure_type,published_at,symbols,company_names,sectors,source,source_ref,language,tags\n1,Test Title,Test Body,FINANCIAL_STATEMENT,2023-01-01T12:00:00Z,ASELS,, ,Source,ref,tr,")

    records = importer.parse_csv(csv_file)
    assert len(records) == 1
    assert records[0].title == "Test Title"
    assert records[0].symbols == ["ASELS"]

def test_disclosure_importer_json(tmp_path):
    importer = DisclosureImporter()
    json_file = tmp_path / "test.json"
    json_file.write_text('[{"external_id": "1", "title": "Test Title JSON", "body": "Test Body JSON", "source": "Source", "language": "tr"}]')

    records = importer.parse_json(json_file)
    assert len(records) == 1
    assert records[0].title == "Test Title JSON"

def test_disclosure_importer_txt(tmp_path):
    importer = DisclosureImporter()
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Test Body TXT")

    record = importer.parse_txt(txt_file)
    assert record.title == "test"
    assert record.body == "Test Body TXT"

def test_disclosure_importer_confirm(tmp_path):
    importer = DisclosureImporter()
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("external_id,title,body,disclosure_type,published_at,symbols,company_names,sectors,source,source_ref,language,tags\n1,Test Title,Test Body,FINANCIAL_STATEMENT,2023-01-01T12:00:00Z,ASELS,, ,Source,ref,tr,")

    result_dry = importer.import_file(csv_file, confirm=False)
    assert result_dry.disclosures_imported == 0
    # Dry run does not parse records so rows_seen is 0
    assert result_dry.rows_seen == 0

def test_disclosure_importer_skip_bad_row(tmp_path):
    importer = DisclosureImporter()
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("external_id,title,body,disclosure_type,published_at,symbols,company_names,sectors,source,source_ref,language,tags\n1,,Test Body,FINANCIAL_STATEMENT,2023-01-01T12:00:00Z,ASELS,, ,Source,ref,tr,\n2,Title,,FINANCIAL_STATEMENT,2023-01-01T12:00:00Z,ASELS,, ,Source,ref,tr,")

    records = importer.parse_csv(csv_file)
    assert len(records) == 0
