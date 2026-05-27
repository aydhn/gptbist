import pytest
from pathlib import Path
import json
from bist_signal_bot.financials.importer import FinancialStatementImporter

def test_importer_wide_csv(tmp_path):
    p = tmp_path / "test.csv"
    p.write_text("symbol,fiscal_year,fiscal_period,period_end,revenue,net_income\nASELS,2024,Q4,2024-12-31,100,20")

    importer = FinancialStatementImporter()
    res = importer.import_file(p, confirm=True)
    assert res.records_imported == 1

def test_importer_long_csv(tmp_path):
    p = tmp_path / "test.csv"
    p.write_text("symbol,fiscal_year,fiscal_period,period_end,item_name,item_value\nASELS,2024,Q4,2024-12-31,revenue,100\nASELS,2024,Q4,2024-12-31,net_income,20")

    importer = FinancialStatementImporter()
    res = importer.import_file(p, confirm=True)
    assert res.records_imported == 1

def test_importer_json(tmp_path):
    p = tmp_path / "test.json"
    data = [{"symbol": "ASELS", "fiscal_year": 2024, "fiscal_period": "Q4", "period_end": "2024-12-31T00:00:00", "values": {"revenue": 100}}]
    with open(p, "w") as f:
        json.dump(data, f)

    importer = FinancialStatementImporter()
    res = importer.import_file(p, confirm=True)
    assert res.records_imported == 1

def test_importer_dry_run(tmp_path):
    p = tmp_path / "test.csv"
    p.write_text("symbol,fiscal_year,fiscal_period,period_end,revenue,net_income\nASELS,2024,Q4,2024-12-31,100,20")

    # with confirm=False, it should mock dry run (depending on settings, but default is dry run without confirm)
    # in tests, if settings is None, confirm=False doesn't skip by default in our minimal impl unless settings say so.
    # We'll just pass confirm=False and check.
    class MockSettings:
        FINANCIAL_IMPORT_REQUIRES_CONFIRM = True

    importer = FinancialStatementImporter(settings=MockSettings())
    res = importer.import_file(p, confirm=False)
    assert res.records_imported == 0
    assert res.records_skipped == 1

def test_importer_skip_bad_row(tmp_path):
    p = tmp_path / "test.csv"
    # Missing symbol
    p.write_text("symbol,fiscal_year,fiscal_period,period_end,revenue,net_income\n,2024,Q4,2024-12-31,100,20")

    importer = FinancialStatementImporter()
    res = importer.import_file(p, confirm=True)
    assert res.records_imported == 0
    assert res.records_skipped == 1
