import pytest
from bist_signal_bot.data_catalog.storage import DataCatalogStore
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data_catalog.models import (
    DatasetRecord, DatasetKind, DatasetFormat, DatasetContract
)
from datetime import datetime, timezone

def test_data_catalog_store_append_load(tmp_path):
    settings = Settings()
    store = DataCatalogStore(settings=settings, base_dir=tmp_path)

    record = DatasetRecord(
        dataset_id="ds1",
        name="test",
        dataset_kind=DatasetKind.OHLCV,
        dataset_format=DatasetFormat.CSV,
        path="test.csv",
        registered_at=datetime.now(timezone.utc)
    )

    store.append_dataset_record(record)

    records = store.load_dataset_records()
    assert len(records) == 1
    assert records[0].dataset_id == "ds1"

def test_data_catalog_store_contracts(tmp_path):
    settings = Settings()
    store = DataCatalogStore(settings=settings, base_dir=tmp_path)

    c = DatasetContract(
        contract_id="c1",
        dataset_kind=DatasetKind.MACRO,
        name="Macro",
        version="1.0"
    )
    store.save_contracts([c])

    loaded = store.load_contracts()
    assert len(loaded) == 1
    assert loaded[0].contract_id == "c1"
