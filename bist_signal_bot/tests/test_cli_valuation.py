from unittest.mock import MagicMock, patch
from bist_signal_bot.cli.valuation_commands import cmd_valuation_config, cmd_valuation_risk

def test_cli_valuation_config():
    args = MagicMock()
    args.json = True
    ctx = MagicMock()
    # explicitly mock the properties so getattr doesn't return a Mock object
    ctx.settings.ENABLE_VALUATION = True
    ctx.settings.VALUATION_SCORE_WEIGHT_HISTORICAL = 0.40

    res = cmd_valuation_config(args, ctx)
    assert res == 0

@patch('bist_signal_bot.cli.valuation_commands.cmd_valuation_show')
def test_cmd_valuation_risk(mock_cmd_valuation_show):
    args = MagicMock()
    ctx = MagicMock()
    mock_cmd_valuation_show.return_value = 0

    res = cmd_valuation_risk(args, ctx)

    assert res == 0
    mock_cmd_valuation_show.assert_called_once_with(args, ctx)
