import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.cli.main import run_cli

def test_cli_benchmarks_list(capsys):
    res = run_cli(["benchmarks", "list"])
    assert res == 0
    out = capsys.readouterr().out
    assert "Registered Benchmarks" in out
    assert "buy_and_hold" in out

def test_cli_benchmarks_run_mock(capsys):
    res = run_cli(["benchmarks", "run", "ASELS", "--benchmark", "buy_and_hold", "--source", "mock"])
    assert res == 0
    out = capsys.readouterr().out
    assert "Benchmark: buy_and_hold" in out
    assert "Status: SUCCESS" in out

def test_cli_benchmarks_batch_mock(capsys):
    res = run_cli(["benchmarks", "batch", "--benchmark", "cash", "--symbols", "ASELS", "GARAN", "--source", "mock"])
    assert res == 0
    out = capsys.readouterr().out
    assert "Benchmark Batch: cash" in out
    assert "Requested Symbols: 2" in out
    assert "Success: 2" in out

def test_cli_benchmarks_default_mock(capsys):
    res = run_cli(["benchmarks", "default", "ASELS", "--source", "mock"])
    assert res == 0
    out = capsys.readouterr().out
    assert "Default Benchmarks for ASELS" in out
    assert "[BUY_AND_HOLD]" in out

def test_cli_healthcheck_benchmarks(capsys):
    res = run_cli(["healthcheck"])
    assert res == 0
    out = capsys.readouterr().out
    assert "benchmarks" in out.lower() or "Healthcheck Raporu" in out
