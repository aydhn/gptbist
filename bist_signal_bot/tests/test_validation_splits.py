import pytest
import pandas as pd
from datetime import datetime
from bist_signal_bot.validation.splits import ValidationSplitBuilder

def test_build_rolling_splits():
    builder = ValidationSplitBuilder()
    splits = builder.build_rolling_splits(
        start=datetime(2020, 1, 1),
        end=datetime(2020, 12, 31),
        train_window_days=100,
        test_window_days=30,
        step_days=30
    )
    assert len(splits) > 0
    assert splits[0].train_start == datetime(2020, 1, 1)

def test_build_purged_kfold_splits():
    builder = ValidationSplitBuilder()
    dates = [datetime(2020, 1, 1) + pd.Timedelta(days=i) for i in range(100)]
    splits = builder.build_purged_kfold_splits(dates, folds=3, purge_days=2, embargo_days=1)
    assert len(splits) == 3

def test_validate_no_overlap_leakage_warning():
    builder = ValidationSplitBuilder()
    from bist_signal_bot.validation.models import ValidationSplit, ValidationSplitType
    s1 = ValidationSplit(
        split_id="1", split_type=ValidationSplitType.CUSTOM,
        train_start=datetime(2020, 1, 1), train_end=datetime(2020, 5, 1),
        test_start=datetime(2020, 4, 1), test_end=datetime(2020, 6, 1),
        fold_index=1
    )
    warnings = builder.validate_no_overlap([s1])
    assert len(warnings) == 1
