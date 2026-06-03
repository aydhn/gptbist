import subprocess
import sys

def run_cmd(args):
    cmd = [sys.executable, "-m", "bist_signal_bot"] + args
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res

def test_cli_market_registry_list():
    res = run_cmd(["market-registry", "list", "--json"])
    assert res.returncode == 0
    assert "BIST_EQUITY" in res.stdout

def test_cli_market_registry_show():
    res = run_cmd(["market-registry", "show", "US_EQUITY_RESEARCH", "--json"])
    assert res.returncode == 0
    assert "US_EQUITY_RESEARCH" in res.stdout

def test_cli_market_registry_instruments():
    res = run_cmd(["market-registry", "instruments", "--market-id", "BIST_EQUITY"])
    assert res.returncode == 0
    assert "ASELS" in res.stdout

def test_cli_market_registry_normalize_symbols():
    res = run_cmd(["market-registry", "normalize-symbols", "AAPL", "MSFT", "--market-id", "US_EQUITY_RESEARCH", "--json"])
    assert res.returncode == 0
    assert "US:AAPL" in res.stdout

def test_cli_market_registry_calendar():
    res = run_cmd(["market-registry", "calendar", "--market-id", "BIST_EQUITY", "--start", "2024-01-01", "--end", "2024-01-05", "--json"])
    assert res.returncode == 0

def test_cli_market_registry_sessions():
    res = run_cmd(["market-registry", "sessions", "--market-id", "BIST_EQUITY", "--date", "2024-01-05", "--json"])
    assert res.returncode == 0

def test_cli_market_registry_universe():
    res = run_cmd(["market-registry", "universe", "--market-id", "BIST_EQUITY", "--json"])
    assert res.returncode == 0

def test_cli_market_registry_validate():
    res = run_cmd(["market-registry", "validate", "--market-id", "BIST_EQUITY", "--symbols", "ASELS", "UNKNOWN", "--json"])
    assert res.returncode == 0

def test_cli_market_registry_governance():
    res = run_cmd(["market-registry", "governance", "--market-id", "BIST_EQUITY", "--json"])
    assert res.returncode == 0

def test_cli_market_registry_report():
    res = run_cmd(["market-registry", "report", "--json"])
    assert res.returncode == 0

def test_cli_market_registry_recent():
    res = run_cmd(["market-registry", "recent", "--json"])
    assert res.returncode == 0

def test_cli_market_registry_config():
    res = run_cmd(["market-registry", "config", "--json"])
    assert res.returncode == 0
