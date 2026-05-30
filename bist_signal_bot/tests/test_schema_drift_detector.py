import pytest
from datetime import datetime, timezone
from bist_signal_bot.data_catalog.schema_drift import SchemaDriftDetector
from bist_signal_bot.data_catalog.models import (
    DatasetContract, DatasetKind, DatasetProfile, DatasetRecord, DatasetFormat
)
from bist_signal_bot.config.settings import Settings

def test_schema_drift_detector():
    settings = Settings()
    detector = SchemaDriftDetector(settings)

    contract = DatasetContract(
        contract_id="c1",
        dataset_kind=DatasetKind.OHLCV,
        name="OHLCV",
        version="1.0",
        required_columns=["date", "close"]
    )

    profile = DatasetProfile(
        profile_id="p1",
        dataset_id="ds1",
        created_at=datetime.now(timezone.utc),
        row_count=10,
        column_count=2,
        columns=["date", "extra_col"],
        detected_format=DatasetFormat.CSV
    )

    record = DatasetRecord(
        dataset_id="ds1",
        name="test",
        dataset_kind=DatasetKind.OHLCV,
        dataset_format=DatasetFormat.CSV,
        path="test.csv",
        registered_at=datetime.now(timezone.utc)
    )

    findings = detector.detect_drift(record, contract, profile)

    # Missing 'close'
    missing = [f for f in findings if f.drift_type.value == "MISSING_COLUMN"]
    assert len(missing) == 1
    assert missing[0].column_name == "close"

    # Extra 'extra_col'
    extra = [f for f in findings if f.drift_type.value == "EXTRA_COLUMN"]
    assert len(extra) == 1
    assert extra[0].column_name == "extra_col"
