import pytest
from datetime import datetime
from bist_signal_bot.validation.models import ValidationSplit, ValidationSplitType, StrategyValidationRequest

def test_validation_split_valid():
    split = ValidationSplit(
        split_id="1",
        split_type=ValidationSplitType.ROLLING,
        train_start=datetime(2020, 1, 1),
        train_end=datetime(2021, 1, 1),
        test_start=datetime(2021, 1, 1),
        test_end=datetime(2022, 1, 1),
        fold_index=1
    )
    assert split.split_id == "1"

def test_validation_split_invalid_dates():
    with pytest.raises(ValueError):
        ValidationSplit(
            split_id="1",
            split_type=ValidationSplitType.ROLLING,
            train_start=datetime(2021, 1, 1),
            train_end=datetime(2020, 1, 1),
            test_start=datetime(2021, 1, 1),
            test_end=datetime(2022, 1, 1),
            fold_index=1
        )

def test_strategy_validation_request_normalization():
    req = StrategyValidationRequest(
        strategy_name="MA",
        symbols=["asels ", " thyao"]
    )
    assert req.symbols == ["ASELS", "THYAO"]
    assert req.strategy_name == "MA"
