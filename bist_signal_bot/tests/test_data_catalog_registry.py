import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data_catalog.registry import DataCatalogRegistry
from bist_signal_bot.data_catalog.models import DatasetKind

def test_data_catalog_registry_discover(tmp_path):
    settings = Settings()
    settings.DATA_CATALOG_DIR_NAME = "data_catalog_test"
    registry = DataCatalogRegistry(settings=settings, base_dir=tmp_path)

    data_dir = tmp_path / "data"
    data_dir.mkdir()
    ohlcv_file = data_dir / "akbnk_ohlcv.csv"
    ohlcv_file.touch()

    records = registry.discover_datasets(root=data_dir, confirm=False)
    assert len(records) == 1
    assert records[0].dataset_kind == DatasetKind.OHLCV

    # Not confirmed, so not in memory dict
    assert len(registry.list_datasets()) == 0

def test_data_catalog_registry_register_confirm(tmp_path):
    settings = Settings()
    registry = DataCatalogRegistry(settings=settings, base_dir=tmp_path)

    csv_path = tmp_path / "financials.csv"
    csv_path.touch()

    record = registry.register_dataset(csv_path, DatasetKind.FINANCIALS, confirm=True)
    assert record.dataset_id in [r.dataset_id for r in registry.list_datasets()]
    assert record.status.value == "ACTIVE"
