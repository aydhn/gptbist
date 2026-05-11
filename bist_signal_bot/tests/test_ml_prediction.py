import pytest
import pandas as pd
from bist_signal_bot.ml.training.prediction import MLPredictor
from bist_signal_bot.ml.training.registry import MLModelRegistry
from bist_signal_bot.ml.training.models import MLPredictionRequest
from bist_signal_bot.config.settings import Settings

class MockRegistry:
    def load_model(self, model_id):
        from sklearn.dummy import DummyClassifier
        est = DummyClassifier(strategy="constant", constant=1)
        est.fit([[0]], [1])
        art = {
            "model_id": model_id,
            "feature_cols": ["feat_1"],
            "task_type": "CLASSIFICATION"
        }
        return est, None, art

def test_predictor_from_dataset():
    settings = Settings()
    predictor = MLPredictor(registry=MockRegistry(), settings=settings)

    df = pd.DataFrame({
        "symbol": ["ASELS", "THYAO"],
        "timestamp": ["2023-01-01", "2023-01-01"],
        "feat_1": [1.0, 2.0]
    })

    res = predictor.predict_from_dataset("test_id", None, df)

    assert res.row_count == 2
    assert res.model_id == "test_id"
    assert len(res.predictions) == 2
    assert float(res.predictions[0].predicted_value) == 1.0

def test_predictor_missing_features():
    settings = Settings()
    predictor = MLPredictor(registry=MockRegistry(), settings=settings)

    df = pd.DataFrame({
        "symbol": ["ASELS"],
        "timestamp": ["2023-01-01"],
        "wrong_feat": [1.0]
    })

    res = predictor.predict_from_dataset("test_id", None, df)

    assert res.row_count == 0
    assert len(res.issues) > 0
