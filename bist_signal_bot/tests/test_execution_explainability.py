import pytest
from bist_signal_bot.explainability.execution_explain import ExecutionExplainer

def test_execution_explainer():
    explainer = ExecutionExplainer()
    payload = {
        "symbol": "ASELS",
        "liquidity_status": "HIGH",
        "cost_bps": 15.0
    }
    res = explainer.explain_execution(payload)
    assert res.liquidity_status == "HIGH"
    assert res.estimated_cost_bps == 15.0
    assert len(res.execution_factors) == 2
