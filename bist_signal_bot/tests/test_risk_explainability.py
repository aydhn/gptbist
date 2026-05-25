import pytest
from bist_signal_bot.explainability.risk_explain import RiskExplainer

def test_risk_explainer():
    explainer = RiskExplainer()
    payload = {
        "symbol": "ASELS",
        "status": "BLOCKED",
        "score": 0.9,
        "blocking_reasons": ["High Volatility"]
    }
    res = explainer.explain_risk(payload)
    assert res.risk_status == "BLOCKED"
    assert "High Volatility" in res.blocking_reasons
