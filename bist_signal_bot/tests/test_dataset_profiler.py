import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data_catalog.profiler import DatasetProfiler
from bist_signal_bot.data_catalog.models import DatasetRecord, DatasetKind, DatasetFormat
from datetime import datetime, timezone

def test_dataset_profiler_csv(tmp_path):
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("a,b\n1,2\n3,4\n1,2")

    settings = Settings()
    profiler = DatasetProfiler(settings=settings, base_dir=tmp_path)

    record = DatasetRecord(
        dataset_id="test_ds",
        name="test",
        dataset_kind=DatasetKind.CUSTOM,
        dataset_format=DatasetFormat.CSV,
        path=str(csv_file),
        registered_at=datetime.now(timezone.utc)
    )

    profile = profiler.profile_dataset(record)
    assert profile.row_count == 3
    assert profile.column_count == 2
    assert "a" in profile.columns
    assert profile.duplicate_count == 1
    assert profile.null_ratios["a"] == 0.0
