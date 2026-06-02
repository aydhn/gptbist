import os
from pathlib import Path

# test_report_templates_core_reports_integration.py
Path("bist_signal_bot/tests/test_report_templates_core_reports_integration.py").write_text('''
from bist_signal_bot.reports.generator import generate_advanced_report
from bist_signal_bot.report_templates.models import ReportTemplateKind, ReportValidationStatus

def test_generate_advanced_report():
    res = generate_advanced_report("daily_research_report_v1", export=False, include_manifest=False)
    assert "report" in res
    rep = res["report"]
    assert rep.template_name == "daily_research_report_v1"
    assert rep.status == ReportValidationStatus.PASS
    assert res["pack"] is None
    assert res["manifest"] is None
''')

# test_report_templates_final_handoff_integration.py
Path("bist_signal_bot/tests/test_report_templates_final_handoff_integration.py").write_text('''
from bist_signal_bot.final_handoff.release_pack import add_report_templates_artifacts

def test_add_report_templates_artifacts():
    pack = {"artifacts": []}
    res = add_report_templates_artifacts(pack)
    assert res == pack
''')

# test_report_templates_qa_ops_integration.py
Path("bist_signal_bot/tests/test_report_templates_qa_ops_integration.py").write_text('''
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
''')

# test_cli_report_templates.py
Path("bist_signal_bot/tests/test_cli_report_templates.py").write_text('''
import subprocess

def test_cli_report_templates_list():
    res = subprocess.run(["python", "-m", "bist_signal_bot", "report-templates", "list", "--json"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "status" in res.stdout
    assert "PASS" in res.stdout

def test_cli_report_templates_show():
    res = subprocess.run(["python", "-m", "bist_signal_bot", "report-templates", "show", "daily_research_report_v1", "--json"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "daily_research_report_v1" in res.stdout
''')

# test_healthcheck_report_templates.py
Path("bist_signal_bot/tests/test_healthcheck_report_templates.py").write_text('''
from bist_signal_bot.app.healthcheck import check_report_templates_health

def test_check_report_templates_health():
    res = check_report_templates_health()
    assert res["report_templates_enabled"] is True
    assert res["latest_validation_status"] == "PASS"
''')

print("Phase 103 Part 13 test files generated.")
