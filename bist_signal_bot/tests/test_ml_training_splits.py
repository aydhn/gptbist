import pytest
import pandas as pd
from bist_signal_bot.ml.training.splits import MLTimeSeriesSplitter
from bist_signal_bot.core.exceptions import MLTrainingValidationError

def test_time_series_split_preserves_order():
    df = pd.DataFrame({
        "timestamp": pd.date_range("2023-01-01", periods=100),
        "feat1": range(100)
    })

    splitter = MLTimeSeriesSplitter()
    train, test = splitter.train_test_split(df, 0.7, "timestamp")

    assert len(train) == 70
    assert len(test) == 30
    assert train["timestamp"].max() < test["timestamp"].min()

def test_time_series_split_empty():
    df = pd.DataFrame()
    splitter = MLTimeSeriesSplitter()
    with pytest.raises(MLTrainingValidationError):
        splitter.train_test_split(df, 0.7, "timestamp")

def test_limit_train_rows():
    df = pd.DataFrame({"feat1": range(100)})
    splitter = MLTimeSeriesSplitter()
    res = splitter.limit_train_rows(df, 20)
    assert len(res) == 20
    assert res.iloc[0]["feat1"] == 80

def test_validate_temporal_order():
    train = pd.DataFrame({"timestamp": pd.date_range("2023-01-01", periods=10)})
    test = pd.DataFrame({"timestamp": pd.date_range("2022-01-01", periods=10)})

    splitter = MLTimeSeriesSplitter()
    with pytest.raises(MLTrainingValidationError):
        splitter.validate_temporal_order(train, test, "timestamp")

def test_split_features_target():
    df = pd.DataFrame({"f1": [1, 2], "f2": [3, 4], "lbl": [0, 1]})
    splitter = MLTimeSeriesSplitter()
    X, y = splitter.split_features_target(df, ["f1", "f2"], "lbl")

    assert list(X.columns) == ["f1", "f2"]
    assert y.name == "lbl"
