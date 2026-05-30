import sys
import pytest
import subprocess

def test_cli_ux_contracts_command():
    result = subprocess.run([sys.executable, "-m", "bist_signal_bot", "cli-ux", "contracts"], capture_output=True, text=True, env={"PYTHONPATH": "."})
    assert result.returncode == 0
    assert "healthcheck" in result.stdout

def test_cli_ux_contracts_json_command():
    result = subprocess.run([sys.executable, "-m", "bist_signal_bot", "cli-ux", "contracts", "--json"], capture_output=True, text=True, env={"PYTHONPATH": "."})
    assert result.returncode == 0
    assert "healthcheck" in result.stdout
    import json
    data = json.loads(result.stdout)
    assert isinstance(data, list)

def test_cli_ux_workflow_dry_run():
    result = subprocess.run([sys.executable, "-m", "bist_signal_bot", "cli-ux", "workflow", "run", "--name", "test", "--dry-run"], capture_output=True, text=True, env={"PYTHONPATH": "."})
    assert result.returncode == 0
    assert "Workflow Run: test" in result.stdout
