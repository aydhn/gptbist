import pytest
from datetime import datetime
import pandas as pd

from bist_signal_bot.validation.walk_forward import WalkForwardValidator
from bist_signal_bot.validation.models import StrategyValidationRequest, ValidationSplit, ValidationSplitType

def test_walk_forward_empty_data():
    validator = WalkForwardValidator()
    req = StrategyValidationRequest(strategy_name="MA")
    res = validator.run("MA", "ASELS", pd.DataFrame(), req, [])
    assert res.status.value == "INSUFFICIENT_DATA"

def test_walk_forward_run_fold():
    validator = WalkForwardValidator()
    split = ValidationSplit(
        split_id="1", split_type=ValidationSplitType.WALK_FORWARD,
        train_start=datetime(2020, 1, 1), train_end=datetime(2020, 5, 1),
        test_start=datetime(2020, 5, 1), test_end=datetime(2020, 6, 1),
        fold_index=1
    )
    res = validator.run_fold("MA", "ASELS", pd.DataFrame(), split, {})
    assert res.fold_id.startswith("FOLD_1")
    assert res.status.value == "PASS"
