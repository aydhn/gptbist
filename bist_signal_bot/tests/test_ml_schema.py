import pytest
import pandas as pd
from bist_signal_bot.ml.schema import MLSchemaBuilder
from bist_signal_bot.ml.models import FeatureConfig, LabelConfig, FeatureSetLevel, LabelType
from bist_signal_bot.core.exceptions import MLSchemaError

def test_build_schema_success():
    builder = MLSchemaBuilder()
    df = pd.DataFrame({"symbol": ["A"], "timestamp": [1], "feat_1": [1], "label_1": [1]})
    fconf = FeatureConfig(feature_set_level=FeatureSetLevel.BASIC)
    lconf = LabelConfig(label_type=LabelType.FORWARD_RETURN, horizon_bars=1)

    schema = builder.build_schema(df, fconf, lconf)
    assert schema.symbol_col == "symbol"
    assert schema.feature_cols == ["feat_1"]
    assert schema.label_cols == ["label_1"]

def test_build_schema_no_features():
    builder = MLSchemaBuilder()
    df = pd.DataFrame({"symbol": ["A"], "label_1": [1]})
    fconf = FeatureConfig(feature_set_level=FeatureSetLevel.BASIC)
    lconf = LabelConfig(label_type=LabelType.FORWARD_RETURN, horizon_bars=1)

    with pytest.raises(MLSchemaError):
        builder.build_schema(df, fconf, lconf)
