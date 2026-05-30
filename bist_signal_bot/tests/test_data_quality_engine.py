import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data_catalog.quality import DataQualityEngine
from bist_signal_bot.data_catalog.models import (
    DatasetRecord, DatasetKind, DatasetFormat, DatasetContract, DatasetProfile,
    DataQualityStatus
)
from datetime import datetime, timezone

def test_data_quality_engine():
    settings = Settings()
    engine = DataQualityEngine(settings=settings)

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
        column_count=1,
        columns=["date"],
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

    assessment = engine.assess(record, contract, profile)

    assert any("close" in f.message for f in assessment.findings if f.rule_name == "required_columns")
    assert assessment.status == DataQualityStatus.FAIL
