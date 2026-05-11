import pytest
from bist_signal_bot.ml.models import LabelConfig, LabelType, FeatureConfig, FeatureSetLevel, PreprocessingConfig, MLDatasetRequest, MLTaskType, DatasetSplitMode

def test_label_config_validation():
    config = LabelConfig(label_type=LabelType.FORWARD_RETURN, horizon_bars=5)
    config.validate_thresholds()

    with pytest.raises(ValueError):
        LabelConfig(label_type=LabelType.BINARY_DIRECTION, horizon_bars=5, positive_threshold=-1, negative_threshold=1).validate_thresholds()

    with pytest.raises(ValueError):
        LabelConfig(label_type=LabelType.BINARY_DIRECTION, horizon_bars=0)

def test_feature_config_defaults():
    config = FeatureConfig(feature_set_level=FeatureSetLevel.BASIC)
    assert config.include_trend is True
    assert config.include_momentum is True

def test_preprocessing_config_validation():
    config = PreprocessingConfig()
    config.validate_winsorize()

    with pytest.raises(ValueError):
        PreprocessingConfig(winsorize_lower_pct=0.99, winsorize_upper_pct=0.01).validate_winsorize()

def test_ml_dataset_request_symbol_normalization():
    req = MLDatasetRequest(
        symbols=["asels", "thyao"],
        source="mock",
        timeframe="1d",
        task_type=MLTaskType.CLASSIFICATION,
        label_config=LabelConfig(label_type=LabelType.FORWARD_RETURN, horizon_bars=1),
        feature_config=FeatureConfig(feature_set_level=FeatureSetLevel.BASIC),
        preprocessing_config=PreprocessingConfig(),
        split_mode=DatasetSplitMode.NONE
    )
    req.validate_request()
    assert req.symbols == ["ASELS", "THYAO"]
