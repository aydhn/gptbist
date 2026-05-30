import pytest
from bist_signal_bot.data_catalog.provenance import SourceProvenanceTracker
from bist_signal_bot.data_catalog.models import DatasetRecord, DatasetKind, DatasetFormat
from datetime import datetime, timezone

def test_source_provenance_checksum(tmp_path):
    tracker = SourceProvenanceTracker()
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")

    checksum = tracker.checksum_path(test_file)
    assert checksum is not None

    record = DatasetRecord(
        dataset_id="ds1",
        name="test",
        dataset_kind=DatasetKind.CUSTOM,
        dataset_format=DatasetFormat.CSV,
        path=str(test_file),
        registered_at=datetime.now(timezone.utc)
    )

    prov = tracker.create_provenance(record, "manual_import", "CSV", str(test_file))
    assert prov.checksum == checksum
    assert prov.trust_level == "MEDIUM"
