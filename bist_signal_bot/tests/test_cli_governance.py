import subprocess
import sys

def run_cli_cmd(cmd: list[str]) -> str:
    result = subprocess.run([sys.executable, "-m", "bist_signal_bot"] + cmd, capture_output=True, text=True)
    return result.stdout + result.stderr

def test_cli_governance_policy():
    out = run_cli_cmd(["governance", "policy"])
    assert "Policy Version:" in out

def test_cli_governance_policy_json():
    out = run_cli_cmd(["governance", "policy", "--json"])
    assert "{" in out
    assert "policy_id" in out

def test_cli_governance_audit():
    out = run_cli_cmd(["governance", "audit"])
    assert "Governance Audit Review" in out

def test_cli_governance_evidence_dry_run():
    out = run_cli_cmd(["governance", "evidence", "--dry-run"])
    assert "Pack Name" in out

def test_cli_governance_config():
    out = run_cli_cmd(["governance", "config"])
    assert "ENABLE_GOVERNANCE" in out
