import pytest
from bist_signal_bot.ml.inference.models import (
    MLInferenceConfig, MLInferenceMode, MLScoreBlendMode
)

def test_ml_inference_config_validation():
    cfg = MLInferenceConfig(model_id="test_model")
    assert cfg.enabled is True
    assert cfg.model_id == "test_model"
    assert cfg.mode == MLInferenceMode.SCORE_AND_FILTER

def test_ml_inference_config_missing_model():
    with pytest.raises(ValueError):
        MLInferenceConfig(enabled=True, model_id=None, model_path=None)

def test_ml_inference_config_disabled_missing_model():
    cfg = MLInferenceConfig(enabled=False, model_id=None, model_path=None)
    assert cfg.enabled is False
    assert cfg.model_id is None
