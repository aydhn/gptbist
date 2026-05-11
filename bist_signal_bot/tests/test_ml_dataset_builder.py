import pytest
import pandas as pd
from unittest.mock import MagicMock
from bist_signal_bot.ml.dataset_builder import MLDatasetBuilder
from bist_signal_bot.ml.models import MLDatasetRequest

def test_single_symbol_dataset_build():
    ds_mock = MagicMock()
    # mock get_data
    ds_mock.get_data.return_value = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=10),
        "open": range(10), "high": range(10), "low": range(10), "close": range(10, 20), "volume": range(10)
    })

    builder = MLDatasetBuilder(data_service=ds_mock)
    req = MLDatasetBuilder.build_default_request(["TEST"]); req.source="mock"
    req.save = False

    res = builder.build_dataset(req)
    assert res.status.value in ["SUCCESS", "PARTIAL_SUCCESS"]
    assert res.symbol_count == 1
    assert "TEST" in res.data["symbol"].values

def test_multi_symbol_dataset_concat():
    ds_mock = MagicMock()
    # returns same df for any symbol
    ds_mock.get_data.return_value = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=10),
        "open": range(10), "high": range(10), "low": range(10), "close": range(10, 20), "volume": range(10)
    })

    builder = MLDatasetBuilder(data_service=ds_mock)
    req = MLDatasetBuilder.build_default_request(["A", "B"]); req.source="mock"
    req.save = False

    res = builder.build_dataset(req)
    assert res.symbol_count == 2
    assert "A" in res.data["symbol"].values
    assert "B" in res.data["symbol"].values

def test_error_in_one_symbol_doesnt_break_all():
    ds_mock = MagicMock()

    def side_effect(symbol, **kwargs):
        if symbol == "B":
            return pd.DataFrame()
        return pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=10),
            "open": range(10), "high": range(10), "low": range(10), "close": range(10, 20), "volume": range(10)
        })

    ds_mock.get_data.side_effect = side_effect

    builder = MLDatasetBuilder(data_service=ds_mock)
    req = MLDatasetBuilder.build_default_request(["A", "B"]); req.source="mock"
    req.save = False

    res = builder.build_dataset(req)
    assert res.symbol_count == 1
    assert "A" in res.data["symbol"].values
    assert len(res.issues) > 0 # B failed

def test_train_test_split_keeps_time_order():
    ds_mock = MagicMock()
    ds_mock.get_data.return_value = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=10),
        "open": range(10), "high": range(10), "low": range(10), "close": range(10, 20), "volume": range(10)
    })
    builder = MLDatasetBuilder(data_service=ds_mock)
    req = MLDatasetBuilder.build_default_request(["A"]); req.source="mock"
    req.train_ratio = 0.5
    req.save = False

    res = builder.build_dataset(req)
    assert len(res.train_data) == 2
    assert len(res.test_data) == 3
    assert res.train_data.iloc[-1]["timestamp"] < res.test_data.iloc[0]["timestamp"]
