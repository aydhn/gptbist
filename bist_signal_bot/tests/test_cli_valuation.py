import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()

from unittest.mock import MagicMock
from bist_signal_bot.cli.valuation_commands import cmd_valuation_config

def test_cli_valuation_config():
    args = MagicMock()
    args.json = True
    ctx = MagicMock()
    # explicitly mock the properties so getattr doesn't return a Mock object
    ctx.settings.ENABLE_VALUATION = True
    ctx.settings.VALUATION_SCORE_WEIGHT_HISTORICAL = 0.40

    res = cmd_valuation_config(args, ctx)
    assert res == 0
