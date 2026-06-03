from bist_signal_bot.explainability.decision_trace import DecisionTraceBuilder
from bist_signal_bot.explainability.models import ExplanationObjectType

def test_decision_trace_builder_steps():
    bld = DecisionTraceBuilder()
    steps_in = [{"step_name": "Check1", "passed": True}]
    trace = bld.build_trace(ExplanationObjectType.STRATEGY, "str_1", steps_in)

    assert len(trace.steps) == 1
    assert trace.steps[0].step_name == "Check1"
    assert trace.status.value == "PASS"

def test_decision_trace_builder_unsafe_output():
    bld = DecisionTraceBuilder()
    # Mocking secret redaction if we can, else just testing output holds
    steps_in = [{"step_name": "Check", "final_output": {"data": "test", "token": "secret123"}}]
    trace = bld.build_trace(ExplanationObjectType.STRATEGY, "str_1", steps_in)
    assert trace.final_output.get("data") == "test"
    assert trace.final_output.get("token") == "***REDACTED***"
