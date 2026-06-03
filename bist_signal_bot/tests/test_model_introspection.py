from bist_signal_bot.explainability.model_introspection import ModelIntrospectionEngine

class MockSKLearnModel:
    def predict(self, rows):
        pass
    feature_names_in_ = ["f1", "f2"]
    feature_importances_ = [0.2, 0.8]

class MockLinearModel:
    def predict(self, rows):
        pass
    feature_names_in_ = ["f1", "f2"]
    coef_ = [0.5, -0.1]

def test_model_introspection_support():
    engine = ModelIntrospectionEngine()
    assert engine.supports_predict(MockSKLearnModel())
    assert engine.supports_feature_importance(MockSKLearnModel())

def test_model_introspection_importances():
    engine = ModelIntrospectionEngine()
    attr = engine.native_feature_importance(MockSKLearnModel())
    assert len(attr) == 2
    assert attr[0].feature_name == "f2" # 0.8 > 0.2

def test_model_introspection_coef():
    engine = ModelIntrospectionEngine()
    attr = engine.native_feature_importance(MockLinearModel())
    assert attr[0].feature_name == "f1"
    assert attr[1].feature_name == "f2"
    assert attr[1].direction.value == "NEGATIVE"
