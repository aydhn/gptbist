import pytest
import pandas as pd
import numpy as np
from bist_signal_bot.ml.training.preprocessing import MLTrainingPreprocessor
from bist_signal_bot.ml.training.models import MLScalerType, MLImputerType

def test_preprocessor_impute_median():
    df_train = pd.DataFrame({"f1": [1, 5, np.nan, 9]})
    prep = MLTrainingPreprocessor(scaler=MLScalerType.NONE, imputer=MLImputerType.MEDIAN)

    res = prep.fit_transform_train(df_train)
    assert res.iloc[2]["f1"] == 5.0

def test_preprocessor_scale_standard():
    df_train = pd.DataFrame({"f1": [10, 20, 30]})
    prep = MLTrainingPreprocessor(scaler=MLScalerType.STANDARD, imputer=MLImputerType.NONE)

    res = prep.fit_transform_train(df_train)
    assert abs(res["f1"].mean()) < 1e-6
    assert abs(res["f1"].std(ddof=0) - 1.0) < 1e-6

def test_preprocessor_drop_non_numeric():
    df_train = pd.DataFrame({"f1": [1, 2], "str_col": ["a", "b"]})
    prep = MLTrainingPreprocessor()
    res = prep.fit_transform_train(df_train)

    assert "str_col" not in res.columns
    assert "f1" in res.columns

def test_preprocessor_test_missing_col():
    df_train = pd.DataFrame({"f1": [1, 2], "f2": [3, 4]})
    prep = MLTrainingPreprocessor()
    prep.fit_transform_train(df_train)

    df_test = pd.DataFrame({"f1": [5, 6]})
    with pytest.raises(Exception):
        prep.transform_test(df_test)
