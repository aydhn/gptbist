import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from bist_signal_bot.data_catalog.models import (
    DatasetRecord, DatasetKind, DatasetFormat, DatasetStatus, DatasetContract
)

def test_dataset_record_validation():
    with pytest.raises(ValidationError):
        DatasetRecord(
            dataset_id="123",
            name="", # Name cannot be empty
            dataset_kind=DatasetKind.OHLCV,
            dataset_format=DatasetFormat.CSV,
            path="some/path",
            registered_at=datetime.now(timezone.utc)
        )

def test_dataset_contract_disclaimer():
    contract = DatasetContract(
        contract_id="c1",
        dataset_kind=DatasetKind.MACRO,
        name="Macro",
        version="1.0"
    )
    assert "local data governance metadata only" in contract.disclaimer
    assert "No real order was sent" in contract.disclaimer
