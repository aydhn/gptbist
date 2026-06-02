import pytest
from pathlib import Path
from bist_signal_bot.data_import.provenance import ImportProvenanceBuilder
from bist_signal_bot.data_import.models import ImportJob, ImportSource, ImportDatasetType, ImportSourceFormat, ImportStatus
from bist_signal_bot.config.settings import Settings
from datetime import datetime, timezone

def test_provenance_checksum(tmp_path):
    f_path = tmp_path / "test.txt"
    f_path.write_text("hello")
    builder = ImportProvenanceBuilder(Settings())
    chk = builder.source_checksum(f_path)
    assert chk is not None

def test_build_provenance(tmp_path):
    f_path = tmp_path / "test.txt"
    f_path.write_text("hello")
    builder = ImportProvenanceBuilder(Settings())

    source = ImportSource(source_id="s1", path=str(f_path), source_format=ImportSourceFormat.CSV, dataset_type=ImportDatasetType.OHLCV, created_at=datetime.now(timezone.utc))
    job = ImportJob(job_id="j1", source=source, started_at=datetime.now(timezone.utc), finished_at=datetime.now(timezone.utc), status=ImportStatus.PASS)

    prov = builder.build_import_provenance(job)
    assert prov["job_id"] == "j1"
    assert prov["source_checksum"] is not None
