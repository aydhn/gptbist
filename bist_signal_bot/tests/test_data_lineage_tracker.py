import pytest
from bist_signal_bot.data_catalog.lineage import DataLineageTracker
from bist_signal_bot.data_catalog.models import LineageRelationType, DatasetRecord, DatasetKind, DatasetFormat
from datetime import datetime, timezone

def test_data_lineage_tracker():
    tracker = DataLineageTracker()

    edge1 = tracker.add_edge("ds1", "ds2", LineageRelationType.DERIVED_FROM)
    edge2 = tracker.add_edge("ds2", "ds3", LineageRelationType.USED_BY)

    assert len(tracker.lineage_for_dataset("ds2")) == 2
    assert len(tracker.lineage_for_dataset("ds1")) == 1

    ds4 = DatasetRecord(
        dataset_id="ds4",
        name="orphan",
        dataset_kind=DatasetKind.CUSTOM,
        dataset_format=DatasetFormat.CSV,
        path="orphan.csv",
        registered_at=datetime.now(timezone.utc)
    )

    orphans = tracker.detect_orphan_datasets([ds4], tracker._edges)
    assert len(orphans) == 1
    assert orphans[0] == "ds4"
