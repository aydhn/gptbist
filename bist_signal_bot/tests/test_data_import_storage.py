import pytest
from pathlib import Path
from bist_signal_bot.data_import.storage import DataImportStore
from bist_signal_bot.data_import.models import ImportJob, ImportSource, ImportDatasetType, ImportSourceFormat, ImportStatus
from bist_signal_bot.config.settings import Settings
from datetime import datetime, timezone

def test_append_load_job(tmp_path):
    settings = Settings()
    settings.DATA_DIR = str(tmp_path)
    store = DataImportStore(settings)

    source = ImportSource(source_id="s1", path="p", source_format=ImportSourceFormat.CSV, dataset_type=ImportDatasetType.OHLCV, created_at=datetime.now(timezone.utc))
    job = ImportJob(job_id="j1", source=source, started_at=datetime.now(timezone.utc), status=ImportStatus.PASS)

    store.append_job(job)
    loaded = store.load_latest_job()
    assert loaded is not None
    assert loaded.job_id == "j1"
