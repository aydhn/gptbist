import pytest
import pandas as pd
from bist_signal_bot.ml.training.trainer import MLModelTrainer
from bist_signal_bot.ml.training.models import MLTrainInput, MLTrainConfig, MLModelType, MLTaskType
from bist_signal_bot.config.settings import Settings

def test_trainer_end_to_end(tmp_path):
    settings = Settings()
    df = pd.DataFrame({
        "timestamp": pd.date_range("2023-01-01", periods=100),
        "symbol": ["ASELS"] * 100,
        "feat_1": range(100),
        "feat_2": range(100, 200),
        "label_1": [0, 1] * 50
    })

    config = MLTrainConfig(
        model_type=MLModelType.DUMMY_CLASSIFIER,
        task_type=MLTaskType.CLASSIFICATION,
        target_col="label_1",
        save_model=False,
        save_report=False
    )

    inp = MLTrainInput(data=df, config=config)
    trainer = MLModelTrainer(settings=settings)

    res = trainer.train(inp)
    assert res.status.value in ["SUCCESS", "PARTIAL_SUCCESS"]
    assert res.artifact is not None
    assert res.classification_metrics is not None

def test_trainer_leakage_target_in_features(tmp_path):
    settings = Settings()
    df = pd.DataFrame({
        "feat_1": range(10),
        "label_1": [0, 1] * 5
    })

    config = MLTrainConfig(
        model_type=MLModelType.DUMMY_CLASSIFIER,
        task_type=MLTaskType.CLASSIFICATION,
        target_col="label_1",
        feature_cols=["feat_1", "label_1"]
    )

    inp = MLTrainInput(data=df, config=config)
    trainer = MLModelTrainer(settings=settings)

    res = trainer.train(inp)
    assert res.status.value == "FAILED"
    assert any("LEAKAGE" in issue for issue in res.issues)
