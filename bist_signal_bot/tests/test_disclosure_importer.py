import pytest
from pathlib import Path
from bist_signal_bot.disclosures.importer import DisclosureImporter
import json
import csv

def test_importer_dry_run_no_save(tmp_path):
    importer = DisclosureImporter()

    # Create fake CSV
    csv_path = tmp_path / "test.csv"
    with open(csv_path, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=["title", "body", "symbols"])
        writer.writeheader()
        writer.writerow({"title": "Test Title", "body": "Test Body", "symbols": "ASELS, THYAO"})

    result = importer.import_file(csv_path, confirm=False)
    assert result.rows_seen == 1
    assert result.disclosures_imported == 0
    assert "Dry run. Import not confirmed." in result.warnings

def test_importer_confirm_save(tmp_path):
    importer = DisclosureImporter()

    # Create fake JSON
    json_path = tmp_path / "test.json"
    with open(json_path, 'w') as f:
        json.dump([
            {"title": "Test Title 1", "body": "Test Body 1", "symbols": ["ASELS"]},
            {"title": "Test Title 2", "body": "Test Body 2", "symbols": ["GARAN"]}
        ], f)

    result = importer.import_file(json_path, confirm=True)
    assert result.rows_seen == 2
    assert result.disclosures_imported == 2

def test_importer_skips_invalid(tmp_path):
    importer = DisclosureImporter()

    json_path = tmp_path / "test.json"
    with open(json_path, 'w') as f:
        json.dump([
            {"title": "", "body": "Test Body 1", "symbols": ["ASELS"]}, # Invalid
            {"title": "Test Title 2", "body": "Test Body 2", "symbols": ["GARAN"]} # Valid
        ], f)

    result = importer.import_file(json_path, confirm=True)
    assert result.rows_seen == 2
    assert result.disclosures_skipped == 1
    assert result.disclosures_imported == 1
