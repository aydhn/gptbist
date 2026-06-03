from bist_signal_bot.explainability.rule_trace import RuleTraceBuilder

def test_rule_trace_moving_average():
    bld = RuleTraceBuilder()
    row = {"ma_50": 100, "ma_200": 80}
    trace = bld.trace_moving_average_strategy(row)
    assert trace.passed_rules == 1
    assert trace.failed_rules == 0
    assert trace.status.value == "PASS"

def test_rule_trace_missing_feature():
    bld = RuleTraceBuilder()
    row = {"ma_50": 100} # ma_200 missing
    trace = bld.trace_moving_average_strategy(row)
    assert trace.status.value == "WATCH"
    assert "Missing feature" in trace.warnings[0]
