import pytest
from unittest.mock import MagicMock
from bist_signal_bot.cli.commands import cmd_universe
from bist_signal_bot.app.bootstrap import ApplicationContext
from bist_signal_bot.config.settings import Settings

class Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

@pytest.fixture
def mock_app_context(tmp_path):
    ctx = MagicMock()
    settings = Settings()
    settings.DATA_DIR = str(tmp_path)
    settings.UNIVERSE_DIR_NAME = "universe"
    settings.UNIVERSE_FILE_NAME = "bist_universe.json"
    settings.WATCHLISTS_DIR_NAME = "watchlists"
    settings.UNIVERSE_SNAPSHOTS_DIR_NAME = "snapshots"
    ctx.settings = settings
    ctx.audit_logger = MagicMock()
    ctx.notifier = MagicMock()
    return ctx

def test_cmd_universe_init(mock_app_context):
    args = Args(universe_command="init", overwrite=False, json=False)
    assert cmd_universe(args, mock_app_context) == 0

def test_cmd_universe_list(mock_app_context):
    # init first
    init_args = Args(universe_command="init", overwrite=False, json=True)
    cmd_universe(init_args, mock_app_context)

    args = Args(universe_command="list", active_only=False, group=None, yfinance=False, json=True)
    assert cmd_universe(args, mock_app_context) == 0

def test_cmd_universe_add(mock_app_context):
    args = Args(universe_command="add", symbol="TEST1", name=None, groups=None, notes=None, json=False)
    assert cmd_universe(args, mock_app_context) == 0

def test_cmd_universe_deactivate(mock_app_context):
    add_args = Args(universe_command="add", symbol="TEST1", name=None, groups=None, notes=None, json=True)
    cmd_universe(add_args, mock_app_context)

    args = Args(universe_command="deactivate", symbol="TEST1", json=False)
    assert cmd_universe(args, mock_app_context) == 0

def test_cmd_universe_watchlist_add(mock_app_context):
    init_args = Args(universe_command="init", overwrite=False, json=True)
    cmd_universe(init_args, mock_app_context)

    args = Args(universe_command="watchlist", watchlist_command="add", name="my_list", symbols=["ASELS"], json=False)
    assert cmd_universe(args, mock_app_context) == 0
