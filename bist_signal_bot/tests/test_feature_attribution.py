import pytest
from bist_signal_bot.explainability.feature_attribution import FeatureAttributionEngine

def test_feature_attribution_top_features():
    engine = FeatureAttributionEngine()
    engine.top_n = 2
    engine.min_abs_score = 0.0
    features = {
        "feat1": 150.0,
        "feat2": -20.0,
        "feat3": 5.0
    }
    contribs = engine.attribute_features(features)
    assert len(contribs) == 2
    assert contribs[0].feature_name == "feat1" # 50.0
    assert contribs[1].feature_name == "feat2" # -20.0

def test_feature_attribution_missing_invalid():
    engine = FeatureAttributionEngine()
    engine.top_n = 10
    engine.min_abs_score = 0.0
    features = {
        "valid": 10.0,
        "invalid": "not_a_number",
        "missing": None
    }
    contribs = engine.attribute_features(features)
    assert len(contribs) == 1
    assert contribs[0].feature_name == "valid"
