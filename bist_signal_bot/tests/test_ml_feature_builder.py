import pytest
import pandas as pd
from bist_signal_bot.ml.feature_builder import MLFeatureBuilder
from bist_signal_bot.ml.models import FeatureConfig, FeatureSetLevel

def test_raw_ohlcv_exclude():
    builder = MLFeatureBuilder()
    df = pd.DataFrame({"open": [1], "high": [2], "low": [1], "close": [2], "volume": [100]})
    config = FeatureConfig(feature_set_level=FeatureSetLevel.BASIC, include_raw_ohlcv=False)
    res = builder.build_features(df, config, "TEST", "1d")
    assert "open" not in res.columns
    assert "close" not in res.columns

def test_return_features_produced():
    builder = MLFeatureBuilder()
    df = pd.DataFrame({"open": [10, 11], "high": [12, 13], "low": [9, 10], "close": [11, 12], "volume": [100, 200]})
    res = builder.add_return_features(df)
    assert "feat_return_1" in res.columns
    assert "feat_log_return_1" in res.columns

def test_standardize_feature_names():
    builder = MLFeatureBuilder()
    df = pd.DataFrame({"close": [1], "sma_10": [2], "label_fwd_return_1": [3], "timestamp": [4]})
    res = builder.standardize_feature_column_names(df)
    assert "feat_sma_10" in res.columns
    assert "sma_10" not in res.columns
    assert "label_fwd_return_1" in res.columns
    assert "close" in res.columns

def test_identify_feature_columns_excludes():
    builder = MLFeatureBuilder()
    df = pd.DataFrame({"close": [1], "feat_1": [2], "label_1": [3], "future_1": [4], "target_1": [5]})
    feats = builder.identify_feature_columns(df)
    assert "feat_1" in feats
    assert "close" not in feats
    assert "label_1" not in feats
    assert "future_1" not in feats
    assert "target_1" not in feats
