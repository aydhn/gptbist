from bist_signal_bot.app.explainability_app import create_risk_explainer
from bist_signal_bot.explainability.risk_explain import RiskExplainer

class MockSettings:
    pass

def test_create_risk_explainer():
    explainer = create_risk_explainer()
    assert isinstance(explainer, RiskExplainer)
    assert explainer.settings is None

def test_create_risk_explainer_with_settings():
    settings = MockSettings()
    explainer = create_risk_explainer(settings=settings)
    assert isinstance(explainer, RiskExplainer)
    assert explainer.settings is settings
