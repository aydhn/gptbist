import pytest
from bist_signal_bot.ops.readiness import check_readiness

def test_ops_readiness_orchestrator():
    res = check_readiness(include_orchestrator=True)
    assert res["status"] == "PASS"
    assert res["research_orchestrator"] == "PASS"
