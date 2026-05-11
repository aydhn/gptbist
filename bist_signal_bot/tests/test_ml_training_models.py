import pytest
from pydantic import ValidationError
from bist_signal_bot.ml.training.models import (
    MLTrainConfig, MLModelType, MLTaskType, MLScalerType, MLImputerType, MLTrainInput
)

def test_ml_train_config_valid():
    config = MLTrainConfig(
        model_type=MLModelType.RANDOM_FOREST_CLASSIFIER,
        task_type=MLTaskType.CLASSIFICATION,
        target_col="label_direction_binary_5",
        scaler=MLScalerType.NONE,
        imputer=MLImputerType.MEDIAN,
        train_ratio=0.8,
        random_seed=42,
        max_train_rows=1000
    )
    assert config.target_col == "label_direction_binary_5"
    assert config.train_ratio == 0.8
    config.validate_config()

def test_ml_train_config_invalid_ratio():
    with pytest.raises(ValidationError):
        MLTrainConfig(
            model_type=MLModelType.RANDOM_FOREST_CLASSIFIER,
            task_type=MLTaskType.CLASSIFICATION,
            target_col="label",
            train_ratio=1.5
        )

def test_ml_train_config_invalid_max_rows():
    with pytest.raises(ValidationError):
        MLTrainConfig(
            model_type=MLModelType.RANDOM_FOREST_CLASSIFIER,
            task_type=MLTaskType.CLASSIFICATION,
            target_col="label",
            max_train_rows=-10
        )

def test_ml_train_config_incompatible_task():
    config = MLTrainConfig(
        model_type=MLModelType.RANDOM_FOREST_REGRESSOR,
        task_type=MLTaskType.CLASSIFICATION,
        target_col="label"
    )
    with pytest.raises(ValueError):
        config.validate_config()

def test_ml_train_input_validation():
    config = MLTrainConfig(
        model_type=MLModelType.RANDOM_FOREST_CLASSIFIER,
        task_type=MLTaskType.CLASSIFICATION,
        target_col="label"
    )
    with pytest.raises(ValueError):
        inp = MLTrainInput(config=config)
        inp.validate_input()

    inp2 = MLTrainInput(config=config, dataset_path="test.csv")
    inp2.validate_input()
