import pytest
from pathlib import Path
from bist_signal_bot.data_import.validation import ImportValidationEngine
from bist_signal_bot.data_import.models import ImportSource, ImportSourceFormat, ImportDatasetType, ImportStatus, ImportPreview
from bist_signal_bot.config.settings import Settings
from datetime import datetime, timezone

def test_check_file_exists(tmp_path):
    ve = ImportValidationEngine(Settings(), tmp_path)
    source = ImportSource(
        source_id="src1", path=str(tmp_path / "not_exists.csv"),
        source_format=ImportSourceFormat.CSV, dataset_type=ImportDatasetType.OHLCV, created_at=datetime.now(timezone.utc)
    )
    findings = ve.check_file_exists(source)
    assert len(findings) == 1
    assert findings[0].status == ImportStatus.FAIL

def test_check_unsafe_path(tmp_path):
    ve = ImportValidationEngine(Settings(), tmp_path)
    source = ImportSource(
        source_id="src1", path="/etc/passwd",
        source_format=ImportSourceFormat.CSV, dataset_type=ImportDatasetType.OHLCV, created_at=datetime.now(timezone.utc)
    )
    findings = ve.check_unsafe_path(source)
    assert len(findings) == 1
    assert findings[0].status == ImportStatus.BLOCKED

def test_duplicate_preview_rows():
    ve = ImportValidationEngine(Settings())
    preview = ImportPreview(
        preview_id="p1", source_id="s1", created_at=datetime.now(timezone.utc),
        column_count=2, columns=["a", "b"],
        sample_rows=[{"a": 1, "b": 2}, {"a": 1, "b": 2}],
        inferred_types={}
    )
    findings = ve.check_duplicate_preview_rows(preview)
    assert len(findings) == 1
    assert findings[0].status == ImportStatus.WATCH
