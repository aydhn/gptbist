import pytest
from bist_signal_bot.qa.release_gate import run_release_gate

def test_qa_release_gate_orchestrator():
    res = run_release_gate(include_orchestrator=True)
    assert res["status"] == "PASS"
    assert "research_orchestrator" in res
    assert res["research_orchestrator"]["no_unsafe_commands"] == "PASS"
