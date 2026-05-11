import pytest
import os
from datetime import datetime
from bist_signal_bot.ml.training.registry import MLModelRegistry
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.ml.training.models import MLModelArtifact, MLModelType, MLTaskType
from sklearn.dummy import DummyClassifier

def test_registry_save_load(tmp_path):
    settings = Settings()
    registry = MLModelRegistry(settings, base_dir=tmp_path)

    estimator = DummyClassifier()
    artifact = MLModelArtifact(
        model_id="test_model_1",
        model_type=MLModelType.DUMMY_CLASSIFIER,
        task_type=MLTaskType.CLASSIFICATION,
        target_col="lbl",
        feature_cols=["f1"],
        model_path="",
        metadata_path="",
        created_at=datetime.now(),
        train_rows=10,
        test_rows=5
    )

    res_art = registry.save_model(estimator, None, artifact)

    assert os.path.exists(res_art.model_path)
    assert os.path.exists(res_art.metadata_path)

    loaded_est, loaded_prep, loaded_art = registry.load_model("test_model_1")
    assert loaded_art.target_col == "lbl"

def test_registry_list_delete(tmp_path):
    settings = Settings()
    registry = MLModelRegistry(settings, base_dir=tmp_path)

    artifact = MLModelArtifact(
        model_id="test_model_2",
        model_type=MLModelType.DUMMY_CLASSIFIER,
        task_type=MLTaskType.CLASSIFICATION,
        target_col="lbl",
        feature_cols=["f1"],
        model_path="",
        metadata_path="",
        created_at=datetime.now(),
        train_rows=10,
        test_rows=5
    )
    registry.save_model(DummyClassifier(), None, artifact)

    models = registry.list_models()
    assert len(models) == 1

    registry.delete_model("test_model_2")
    models2 = registry.list_models()
    assert len(models2) == 0
