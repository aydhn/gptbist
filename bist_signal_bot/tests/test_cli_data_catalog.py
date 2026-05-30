import pytest
import sys
from io import StringIO
from unittest.mock import patch

from bist_signal_bot.cli_ux.data_catalog_cli import run_data_catalog_cli

def test_cli_data_catalog_contracts_list():
    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
        run_data_catalog_cli(["contracts", "list", "--json"])
        out = mock_stdout.getvalue()
        assert "contract_id" in out
        assert "OHLCV" in out

def test_cli_data_catalog_register_dry_run():
    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
        run_data_catalog_cli(["register", "--path", "test.csv", "--kind", "OHLCV", "--dry-run", "--json"])
        out = mock_stdout.getvalue()
        assert "test.csv" in out
        assert "OHLCV" in out

def test_cli_data_catalog_report():
    with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
        run_data_catalog_cli(["report", "--json"])
        out = mock_stdout.getvalue()
        assert "status" in out
