import pytest
import pandas as pd
from bist_signal_bot.ml.leakage import MLLeakageGuard
from bist_signal_bot.ml.models import MLDatasetSchema
from bist_signal_bot.core.exceptions import MLLeakageError

def test_future_feature_columns():
    guard = MLLeakageGuard()
    df = pd.DataFrame()
    issues = guard.validate_no_future_feature_columns(df, ["feat_1", "feat_future_ret", "label_leak"])
    assert len(issues) == 2
    assert any("feat_future_ret" in i for i in issues)
    assert any("label_leak" in i for i in issues)

def test_label_not_in_features():
    guard = MLLeakageGuard()
    with pytest.raises(MLLeakageError):
        guard.validate_label_not_in_features(["feat_1", "label_1"], ["label_1"])

def test_time_order():
    guard = MLLeakageGuard()
    df = pd.DataFrame({"timestamp": [2, 1, 3]})
    with pytest.raises(MLLeakageError):
        guard.validate_time_order(df)

    df2 = pd.DataFrame({"timestamp": [1, 2, 3]})
    guard.validate_time_order(df2) # should pass
