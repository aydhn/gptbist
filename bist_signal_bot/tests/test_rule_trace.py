import pytest
from bist_signal_bot.explainability.rule_trace import RuleTraceBuilder

def test_trace_moving_average():
    builder = RuleTraceBuilder()
    row = {"close": 110, "sma_50": 100}
    trace = builder.build_trace("moving_average_trend", "ASELS", row)
    assert trace.strategy_name == "moving_average_trend"
    assert trace.passed_count == 1
    assert trace.failed_count == 0
    assert len(trace.steps) == 1
    assert trace.steps[0].passed is True

def test_trace_generic():
    builder = RuleTraceBuilder()
    row = {"close": 110}
    trace = builder.build_trace("unknown_strategy", "ASELS", row)
    assert len(trace.steps) == 1
    assert trace.steps[0].rule_name == "Generic condition"
    assert trace.steps[0].passed is True
