import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
import sys
from unittest.mock import patch
from io import StringIO
import json

from bist_signal_bot.cli.main import run_cli
from bist_signal_bot.config.settings import settings

def run_cmd(args_list):
    test_args = ["bist_signal_bot"] + args_list
    with patch.object(sys, 'argv', test_args):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            try:
                 run_cli()
            except SystemExit as e:
                 if e.code != 0:
                      raise Exception(f"Command failed with {e.code}: {fake_out.getvalue()}")
            return fake_out.getvalue()

def test_cli_paper_init(tmp_path):
    # 36. CLI paper init çalışır.
    settings.PAPER_ACCOUNTS_DIR_NAME = "test_paper_accounts"
    settings.DATA_DIR = str(tmp_path)

    out = run_cmd(["paper", "init", "--account", "test_cli", "--cash", "1500"])
    assert "Account test_cli initialized" in out

def test_cli_paper_status(tmp_path):
    # 37. CLI paper status çalışır.
    settings.PAPER_ACCOUNTS_DIR_NAME = "test_paper_accounts"
    settings.DATA_DIR = str(tmp_path)
    run_cmd(["paper", "init", "--account", "test_cli_status"])

    out = run_cmd(["paper", "status", "--account", "test_cli_status"])
    assert "Account ID : test_cli_status" in out

def test_cli_paper_run_once(tmp_path):
    # 38. CLI paper run-once --source mock çalışır.
    # 39. CLI paper run-once --json valid JSON üretir.
    settings.PAPER_ACCOUNTS_DIR_NAME = "test_paper_accounts"
    settings.DATA_DIR = str(tmp_path)
    run_cmd(["paper", "init", "--account", "test_cli_run"])

    out = run_cmd(["paper", "run-once", "ASELS", "--source", "mock", "--strategy", "moving_average_trend", "--account", "test_cli_run"])
    assert "Paper Trading Run Result" in out

    out_json = run_cmd(["paper", "run-once", "ASELS", "--source", "mock", "--strategy", "moving_average_trend", "--account", "test_cli_run", "--json"])
    data = json.loads(out_json)
    assert data["account"]["account_id"] == "test_cli_run"

def test_cli_paper_lists(tmp_path):
    # 40. CLI paper positions/orders/fills/trades çalışır.
    settings.PAPER_ACCOUNTS_DIR_NAME = "test_paper_accounts"
    settings.DATA_DIR = str(tmp_path)
    run_cmd(["paper", "init", "--account", "test_cli_lists"])

    out1 = run_cmd(["paper", "positions", "--account", "test_cli_lists"])
    assert "No open positions" in out1

    out2 = run_cmd(["paper", "orders", "--account", "test_cli_lists"])
    assert "No orders found" in out2

def test_cli_paper_reset_confirm():
    # 41. CLI paper reset --confirm olmadan reddedilir.
    with pytest.raises(Exception) as exc:
         run_cmd(["paper", "reset", "--account", "test_acc"])
    assert "You must provide --confirm" in str(exc.value)

def test_cli_paper_export(tmp_path):
    # 42. CLI paper export çalışır.
    settings.PAPER_ACCOUNTS_DIR_NAME = "test_paper_accounts"
    settings.DATA_DIR = str(tmp_path)
    run_cmd(["paper", "init", "--account", "test_export"])

    out = run_cmd(["paper", "export", "--account", "test_export"])
    assert "Exported orders" in out

def test_cli_paper_config():
    # 43. CLI paper config secret sızdırmaz.
    out = run_cmd(["paper", "config"])
    assert "ENABLE_PAPER_TRADING" in out
    assert "PAPER_DEFAULT_ACCOUNT_ID" in out
