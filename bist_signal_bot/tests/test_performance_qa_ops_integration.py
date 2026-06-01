import pytest
from bist_signal_bot.qa.release_gate import check_performance
from bist_signal_bot.ops.readiness import check_readiness

def test_qa_release_gate_performance():
    report = {}
    check_performance(report)
    assert "performance" in report
    assert report["performance"]["status"] == "PASS"

def test_ops_readiness_performance():
    res = check_readiness(include_performance=True)
    assert "performance" in res
    assert res["performance"] == "PASS"
