import pytest
import pandas as pd
import numpy as np
from bist_signal_bot.ml.preprocessing import MLPreprocessor
from bist_signal_bot.ml.models import PreprocessingConfig

def test_remove_inf():
    prep = MLPreprocessor()
    df = pd.DataFrame({"feat_1": [1, np.inf, -np.inf, 4]})
    res = prep.remove_inf_values(df)
    assert pd.isna(res.iloc[1, 0])
    assert pd.isna(res.iloc[2, 0])

def test_fill_median():
    prep = MLPreprocessor()
    df = pd.DataFrame({"feat_1": [1, 3, np.nan, 5]})
    res = prep.fill_missing(df, ["feat_1"], "median")
    assert res.iloc[2, 0] == 3.0

def test_drop_na_labels():
    prep = MLPreprocessor()
    df = pd.DataFrame({"feat_1": [1, 2], "label_1": [1, np.nan]})
    config = PreprocessingConfig(drop_na_labels=True, remove_inf=False, fill_method="none", winsorize=False)
    res = prep.preprocess(df, config, ["feat_1"], ["label_1"])
    assert len(res) == 1

def test_winsorize():
    prep = MLPreprocessor()
    df = pd.DataFrame({"feat_1": [1, 2, 3, 4, 100]})
    # 0.2, 0.8 percentiles
    res = prep.winsorize_features(df, ["feat_1"], 0.2, 0.8)
    assert res.iloc[4, 0] < 100

def test_standardize_default_false():
    config = PreprocessingConfig()
    assert config.standardize is False
