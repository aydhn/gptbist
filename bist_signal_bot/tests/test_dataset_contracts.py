import pytest
from bist_signal_bot.data_catalog.contracts import DatasetContractRegistry
from bist_signal_bot.data_catalog.models import DatasetKind, DatasetContract, DatasetFormat

def test_contract_registry_loads_defaults():
    registry = DatasetContractRegistry()
    contracts = registry.default_contracts()

    assert len(contracts) > 0
    ohlcv = registry.get_contract(DatasetKind.OHLCV)
    assert ohlcv is not None
    assert "close" in ohlcv.required_columns

def test_contract_validation():
    registry = DatasetContractRegistry()
    invalid_contract = DatasetContract(
        contract_id="test",
        dataset_kind=DatasetKind.CUSTOM,
        name="test",
        version="1.0",
        required_columns=[] # Invalid, must have at least one
    )
    errors = registry.validate_contract(invalid_contract)
    assert len(errors) > 0
    assert "must specify at least one required column" in errors[0]

def test_contract_for_path():
    registry = DatasetContractRegistry()

    from pathlib import Path

    c1 = registry.contract_for_path(Path("ISBANK_OHLCV.csv"))
    assert c1 is not None
    assert c1.dataset_kind == DatasetKind.OHLCV

    c2 = registry.contract_for_path(Path("ISBANK_adjusted_ohlcv.csv"))
    assert c2 is not None
    assert c2.dataset_kind == DatasetKind.ADJUSTED_OHLCV

    c3 = registry.contract_for_path(Path("balance_sheet_2023.parquet"))
    assert c3 is not None
    assert c3.dataset_kind == DatasetKind.FINANCIALS

    c4 = registry.contract_for_path(Path("unknown_data.csv"))
    assert c4 is None
