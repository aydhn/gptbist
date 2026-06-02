
from bist_signal_bot.qa.release_gate import check_report_templates_release_gate
from bist_signal_bot.governance.gate import GovernanceGate

def test_qa_release_gate_report_templates():
    res = check_report_templates_release_gate()
    assert res["status"] == "PASS"

def test_governance_report_templates_safe():
    gate = GovernanceGate()
    res1 = gate.check_report_templates_safe("Bu test")
    assert res1["status"] == "PASS"
    res2 = gate.check_report_templates_safe("Kesin trade ready al/sat")
    assert res2["status"] == "BLOCK"
