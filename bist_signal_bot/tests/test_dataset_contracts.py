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
