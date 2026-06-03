from bist_signal_bot.explainability.feature_attribution import FeatureAttributionEngine

def test_feature_attribution_engine_simple():
    engine = FeatureAttributionEngine()
    row = {"feat1": 150.5, "feat2": -45.0, "feat3": "string_val"}
    attrs = engine.simple_attribution(row)

    assert len(attrs) == 3
    feat3_attr = next(a for a in attrs if a.feature_name == "feat3")
    assert feat3_attr.contribution_score is None
    assert len(feat3_attr.warnings) > 0

def test_feature_attribution_rank():
    engine = FeatureAttributionEngine()
    row = {"f1": 10, "f2": 50, "f3": -80}
    attrs = engine.simple_attribution(row)
    ranked = engine.rank_attributions(attrs)
    assert ranked[0].feature_name == "f3"
    assert ranked[1].feature_name == "f2"
    assert ranked[2].feature_name == "f1"
