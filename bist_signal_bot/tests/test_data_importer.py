import pytest
from pathlib import Path
from bist_signal_bot.data_import.importer import LocalDataImporter
from bist_signal_bot.data_import.models import ImportDatasetType, ImportStatus
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import LocalDataImporterError

def test_dry_run_does_not_write(tmp_path):
    importer = LocalDataImporter(Settings(), tmp_path)
    csv_path = tmp_path / "test.csv"
    csv_path.write_text("symbol,date,open,high,low,close,volume\nTHYAO,2024-01-01,10,12,9,11,100")

    out_dir = tmp_path / "out"
    job = importer.run_import(csv_path, ImportDatasetType.OHLCV, out_dir, dry_run=True)

    assert job.status == ImportStatus.DRY_RUN
    assert not out_dir.exists()

def test_confirm_without_dry_run_writes(tmp_path):
    importer = LocalDataImporter(Settings(), tmp_path)
    csv_path = tmp_path / "test.csv"
    csv_path.write_text("symbol,date,open,high,low,close,volume\nTHYAO,2024-01-01,10,12,9,11,100")

    out_dir = tmp_path / "out"
    job = importer.run_import(csv_path, ImportDatasetType.OHLCV, out_dir, dry_run=False, confirm=True)

    assert job.status == ImportStatus.PASS
    assert out_dir.exists()
    assert list(out_dir.glob("*.parquet"))

def test_write_requires_confirm(tmp_path):
    importer = LocalDataImporter(Settings(), tmp_path)
    csv_path = tmp_path / "test.csv"
    csv_path.write_text("symbol,date,open,high,low,close,volume\nTHYAO,2024-01-01,10,12,9,11,100")

    with pytest.raises(LocalDataImporterError):
        importer.run_import(csv_path, ImportDatasetType.OHLCV, tmp_path / "out", dry_run=False, confirm=False)
