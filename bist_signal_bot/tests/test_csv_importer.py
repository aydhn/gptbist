import pytest
import pandas as pd
from bist_signal_bot.data.importers.csv_importer import CSVMarketDataImporter
from bist_signal_bot.data.providers_v2.models import ImportRequest, DataImportStatus

def test_csv_importer(tmp_path):
    df = pd.DataFrame({
        'tarih': ['2023-01-01', '2023-01-02'],
        'açılış': [10, 11],
        'yüksek': [12, 13],
        'düşük': [9, 10],
        'kapanış': [11, 12],
        'hacim': [100, 200]
    })
    path = tmp_path / "ASELS.csv"
    df.to_csv(path, index=False)

    importer = CSVMarketDataImporter()
    req = ImportRequest(input_path=str(path), timeframe="1d", format="csv")
    res = importer.import_file(req)

    assert res.status == DataImportStatus.IMPORTED
    assert res.symbol == "ASELS"
    assert res.rows_imported == 2
    assert res.lineage is not None

    parsed_df = res.metadata.get("_parsed_df")
    assert parsed_df is not None
    assert 'date' in parsed_df.columns
    assert 'close' in parsed_df.columns

def test_csv_importer_missing_file():
    importer = CSVMarketDataImporter()
    req = ImportRequest(input_path="does_not_exist.csv", timeframe="1d", format="csv")
    res = importer.import_file(req)
    assert res.status == DataImportStatus.FAILED
