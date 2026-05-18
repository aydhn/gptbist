import pytest
import pandas as pd
from bist_signal_bot.data.importers.parquet_importer import ParquetMarketDataImporter
from bist_signal_bot.data.providers_v2.models import ImportRequest, DataImportStatus

def test_parquet_importer(tmp_path):
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01', '2023-01-02']),
        'open': [10, 11],
        'high': [12, 13],
        'low': [9, 10],
        'close': [11, 12],
        'volume': [100, 200]
    })
    path = tmp_path / "THYAO.parquet"
    df.to_parquet(path, index=False)

    importer = ParquetMarketDataImporter()
    req = ImportRequest(input_path=str(path), timeframe="1d", format="parquet")
    res = importer.import_file(req)

    assert res.status == DataImportStatus.IMPORTED
    assert res.symbol == "THYAO"
    assert res.rows_imported == 2
    assert res.lineage is not None
