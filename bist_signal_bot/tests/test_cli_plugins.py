import pytest
import subprocess

def test_cli_plugins_discover():
    res = subprocess.run(["python3", "-m", "bist_signal_bot", "plugins", "discover"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "Discovered" in res.stdout

def test_cli_plugins_validate():
    res = subprocess.run(["python3", "-m", "bist_signal_bot", "plugins", "validate", "--plugin", "example_strategy_plugin"], capture_output=True, text=True)
    assert res.returncode == 0

def test_cli_healthcheck_plugins():
    res = subprocess.run(["python3", "-m", "bist_signal_bot", "healthcheck", "--plugins"], capture_output=True, text=True)
    assert res.returncode == 0
