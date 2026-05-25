import pytest
from bist_signal_bot.explainability.ml_explain import MLExplainer

class MockModel:
    def __init__(self):
        self.feature_importances_ = [0.1, 0.9]

class MockModelErr:
    @property
    def feature_importances_(self):
        raise ValueError("Error fetching importances")

def test_ml_explainer_feature_importances():
    explainer = MLExplainer()
    model = MockModel()
    res = explainer.explain_prediction(model, {"f1": 10, "f2": 20})
    assert res.method == "feature_importances"
    assert len(res.top_features) == 2
    assert res.top_features[1].feature_name == "f2"

def test_ml_explainer_fallback():
    explainer = MLExplainer()
    model = MockModelErr()
    res = explainer.explain_prediction(model, {"f1": 10})
    assert res.method == "fallback"
    assert "WARN" in res.status
