import pytest
from datetime import datetime, timezone
from bist_signal_bot.data_catalog.reporting import format_data_catalog_report_markdown
from bist_signal_bot.data_catalog.models import (
    DataCatalogReport, DatasetRecord, DatasetKind, DatasetFormat, DatasetStatus,
    DataQualityGateResult, DataQualityStatus
)

def test_format_data_catalog_report():
    report = DataCatalogReport(
        report_id="1",
        generated_at=datetime.now(timezone.utc),
        datasets=[
             DatasetRecord(
                 dataset_id="ds1",
                 name="Test",
                 dataset_kind=DatasetKind.OHLCV,
                 dataset_format=DatasetFormat.CSV,
                 path="test.csv",
                 registered_at=datetime.now(timezone.utc),
                 status=DatasetStatus.ACTIVE
             )
        ],
        gates=[
             DataQualityGateResult(
                 gate_id="g1",
                 gate_name="default",
                 created_at=datetime.now(timezone.utc),
                 status=DataQualityStatus.PASS,
                 actual_score=100.0
             )
        ]
    )

    md = format_data_catalog_report_markdown(report)
    assert "Data Catalog & Quality Report" in md
    assert "Test (ds1)" in md
    assert "Gate **default**: PASS (Score: 100.0)" in md
    assert "No real order was sent." in md
