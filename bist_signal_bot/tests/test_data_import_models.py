import pytest
from datetime import datetime, timezone
from bist_signal_bot.data_import.models import (
    ImportStatus, ImportSourceFormat, ImportDatasetType,
    ImportSource, SchemaMapping, ImportJob, ImportPreview
)

def test_import_source_model():
    source = ImportSource(
        source_id="src-1",
        path="data/test.csv",
        source_format=ImportSourceFormat.CSV,
        dataset_type=ImportDatasetType.OHLCV,
        created_at=datetime.now(timezone.utc)
    )
    assert source.path == "data/test.csv"
    assert source.source_format == ImportSourceFormat.CSV

def test_schema_mapping_disclaimer():
    mapping = SchemaMapping(
        schema_mapping_id="map-1",
        dataset_type=ImportDatasetType.OHLCV,
        source_columns=["a"],
        column_mappings=[],
        unmapped_columns=["a"],
        missing_required_targets=["symbol"]
    )
    assert "not investment advice" in mapping.disclaimer.lower()

def test_import_job_disclaimer():
    source = ImportSource(
        source_id="src-1",
        path="data/test.csv",
        source_format=ImportSourceFormat.CSV,
        dataset_type=ImportDatasetType.OHLCV,
        created_at=datetime.now(timezone.utc)
    )
    job = ImportJob(
        job_id="job-1",
        source=source,
        started_at=datetime.now(timezone.utc),
        dry_run=True,
        status=ImportStatus.DRY_RUN
    )
    assert "not investment advice" in job.disclaimer.lower()
