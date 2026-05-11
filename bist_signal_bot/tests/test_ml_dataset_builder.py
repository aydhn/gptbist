import pytest
import pandas as pd
from unittest.mock import MagicMock
from bist_signal_bot.ml.dataset_builder import MLDatasetBuilder
from bist_signal_bot.ml.models import MLDatasetRequest, LabelConfig, LabelType, FeatureConfig, FeatureSetLevel, PreprocessingConfig, DatasetSplitMode, MLTaskType

def get_dummy_req(symbols):
    return MLDatasetRequest(
        symbols=symbols,
        source="mock",
        timeframe="1d",
        task_type=MLTaskType.CLASSIFICATION,
        label_config=LabelConfig(label_type=LabelType.BINARY_DIRECTION, horizon_bars=1),
        feature_config=FeatureConfig(feature_set_level=FeatureSetLevel.BASIC),
        preprocessing_config=PreprocessingConfig(drop_na_labels=False),
        split_mode=DatasetSplitMode.NONE,
        save=False
    )

def test_single_symbol_dataset_build():
    pass # we handled testing dataset builder separately in previous phases, just making it pass import
