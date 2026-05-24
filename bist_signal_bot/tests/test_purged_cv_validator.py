import pytest
from datetime import datetime
import pandas as pd

from bist_signal_bot.validation.purged_cv import PurgedCVValidator
from bist_signal_bot.validation.models import StrategyValidationRequest, ValidationSplit, ValidationSplitType

def test_purged_cv_empty_data():
    validator = PurgedCVValidator()
    req = StrategyValidationRequest(strategy_name="MA")
    res = validator.run("MA", "ASELS", pd.DataFrame(), req, [])
    assert res.status.value == "INSUFFICIENT_DATA"

def test_purged_cv_leakage_warning():
    validator = PurgedCVValidator()
    split = ValidationSplit(
        split_id="1", split_type=ValidationSplitType.PURGED_K_FOLD,
        train_start=datetime(2020, 1, 1), train_end=datetime(2020, 5, 1),
        test_start=datetime(2020, 5, 1), test_end=datetime(2020, 6, 1),
        fold_index=1, purge_days=0, embargo_days=0
    )
    warnings = validator.detect_leakage_risk([split])
    assert len(warnings) == 1
    assert "High leakage risk" in warnings[0]
