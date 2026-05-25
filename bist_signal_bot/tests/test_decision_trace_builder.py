import pytest
from bist_signal_bot.explainability.decision_trace import DecisionTraceBuilder

def test_decision_trace_builder():
    builder = DecisionTraceBuilder()
    payload = {"symbol": "ASELS"}
    stages = {
        "data_loaded": {"status": "PASS", "message": "OK"},
        "risk_checked": {"status": "FAIL", "message": "Risk limit exceeded"}
    }
    trace = builder.build_trace(payload, stages)
    assert trace.symbol == "ASELS"
    assert trace.final_decision == "BLOCKED"
    assert trace.blocked is True
    assert "Risk limit exceeded" in trace.blocked_reasons
