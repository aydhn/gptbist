import pytest
import pandas as pd
import numpy as np
from bist_signal_bot.ml.labels import LabelBuilder
from bist_signal_bot.ml.models import LabelConfig, LabelType

def test_forward_return_label():
    builder = LabelBuilder()
    df = pd.DataFrame({"close": [100, 105, 110.25]})
    fwd = builder.forward_return(df, horizon_bars=1)

    assert fwd.name == "label_fwd_return_1"
    assert round(fwd.iloc[0], 2) == 0.05
    assert round(fwd.iloc[1], 2) == 0.05
    assert pd.isna(fwd.iloc[-1])

def test_binary_direction_label():
    builder = LabelBuilder()
    fwd = pd.Series([-0.05, 0.01, 0.05, np.nan], name="label_fwd_return_1")
    lbl = builder.binary_direction_label(fwd, positive_threshold=0.02)
    assert lbl.iloc[0] == 0
    assert lbl.iloc[1] == 0
    assert lbl.iloc[2] == 1
    assert pd.isna(lbl.iloc[3])

def test_multiclass_direction_label():
    builder = LabelBuilder()
    fwd = pd.Series([-0.05, 0.01, 0.05, np.nan], name="label_fwd_return_1")
    lbl = builder.multiclass_direction_label(fwd, 0.02, -0.02)
    assert lbl.iloc[0] == -1
    assert lbl.iloc[1] == 0
    assert lbl.iloc[2] == 1
    assert pd.isna(lbl.iloc[3])

def test_last_horizon_nan():
    builder = LabelBuilder()
    df = pd.DataFrame({"close": [1, 2, 3, 4, 5]})
    config = LabelConfig(label_type=LabelType.FORWARD_RETURN, horizon_bars=2)
    res = builder.add_labels(df, config)
    assert pd.isna(res.iloc[-1]["label_fwd_return_2"])
    assert pd.isna(res.iloc[-2]["label_fwd_return_2"])

def test_label_not_in_features():
    builder = LabelBuilder()
    config = LabelConfig(label_type=LabelType.FORWARD_RETURN, horizon_bars=1)
    cols = builder.label_columns_for_config(config)
    assert all(c.startswith("label_") for c in cols)

def test_volatility_adjusted_issue():
    builder = LabelBuilder()
    df = pd.DataFrame({"close": [10, 11]})
    fwd = pd.Series([0.1, np.nan], name="label_fwd_return_1")
    lbl = builder.volatility_adjusted_return(df, fwd)
    # no volatility col, should fallback to unadjusted
    assert lbl.iloc[0] == 0.1
