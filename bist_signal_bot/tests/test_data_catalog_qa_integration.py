import pytest
from bist_signal_bot.qa.release_gate import run_release_gate

def test_qa_release_gate_includes_data_catalog():
    res = run_release_gate(include_data_catalog=True)
    assert "data_catalog" in res
    assert res["data_catalog"]["gate_status"] == "PASS"
