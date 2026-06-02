
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
